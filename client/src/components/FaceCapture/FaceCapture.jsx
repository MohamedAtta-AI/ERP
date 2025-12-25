import React, { useEffect, useRef, useState, useCallback } from "react";
import { faceDetectionService } from "../../services/faceDetectionService";
import styles from "./FaceCapture.module.css";

// Production-quality thresholds
const QUALITY_THRESHOLDS = {
  BRIGHTNESS_MIN: 60,
  BRIGHTNESS_MAX: 200,
  SHARPNESS_MIN: 1.5,
  FACE_SIZE_MIN: 0.05,
  FACE_SIZE_MAX: 0.5,
  // For center pose
  YAW_MAX: 15,
  PITCH_MAX: 15,
  ROLL_MAX: 12,
};

const POSE_SMOOTHING = {
  EMA_ALPHA: 0.3,
};

// Auto-capture settings
const AUTO_CAPTURE = {
  STABILITY_DURATION: 800,
  BURST_COUNT: 3,
  BURST_INTERVAL: 100,
  COOLDOWN: 1500,
};

// Multi-angle poses for registration
const CAPTURE_POSES = [
  { id: "center", label: "Look straight", targetYaw: 0, yawTolerance: 20 },
  { id: "left", label: "Turn head LEFT", targetYaw: 30, yawTolerance: 15 },
  { id: "right", label: "Turn head RIGHT", targetYaw: -30, yawTolerance: 15 },
];

const FaceCapture = ({
  onCapture,
  onMultiCapture, // For multi-angle: receives array of files
  onCancel,
  requiresLiveness = false, // Ignored now - we use multi-angle instead
  mode = "registration", // "registration" = multi-angle, "attendance" = single
}) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const analysisCanvasRef = useRef(null);
  const landmarksCanvasRef = useRef(null); // For drawing landmarks
  const streamRef = useRef(null);
  const detectionIntervalRef = useRef(null);
  const lastCaptureTimeRef = useRef(0);
  const stabilityStartRef = useRef(null);
  const poseEmaRef = useRef(null);
  const faceDataRef = useRef(null); // Use ref instead of state for capture

  const [cameraState, setCameraState] = useState("initializing");
  const [error, setError] = useState(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const [autoCaptureEnabled, setAutoCaptureEnabled] = useState(true);

  // Multi-angle capture state
  const [currentPoseIndex, setCurrentPoseIndex] = useState(0);
  const [capturedImages, setCapturedImages] = useState([]); // Array of captured images
  const [poseMatched, setPoseMatched] = useState(false);

  // Detection results
  const [detectedFace, setDetectedFace] = useState(null);
  const [faceData, setFaceData] = useState(null);

  // Quality check states
  const [qualityChecks, setQualityChecks] = useState({
    faceDetected: { passed: false, message: "Loading..." },
    faceSize: { passed: false, value: 0, message: "Waiting..." },
    pose: { passed: false, message: "Checking..." },
    brightness: { passed: false, value: 0, message: "Checking..." },
    sharpness: { passed: false, value: 0, message: "Checking..." },
  });
  const [passedCount, setPassedCount] = useState(0);
  const [allChecksPassed, setAllChecksPassed] = useState(false);
  const [qualityStable, setQualityStable] = useState(false);

  // Get current target pose
  const isMultiAngle = mode === "registration";
  const currentPose = isMultiAngle
    ? CAPTURE_POSES[currentPoseIndex]
    : CAPTURE_POSES[0];
  const totalPoses = isMultiAngle ? CAPTURE_POSES.length : 1;

  // Check if models are already loaded
  useEffect(() => {
    const checkModels = async () => {
      try {
        await faceDetectionService.ensureModelsLoaded();
        setModelsLoaded(true);
      } catch (err) {
        console.error("Failed to load face detection models:", err);
        setError("Failed to load face detection. Please refresh.");
      }
    };
    checkModels();
  }, []);

  // Start camera
  const startCamera = useCallback(async () => {
    if (streamRef.current) return;

    setCameraState("initializing");
    setError(null);

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
        audio: false,
      });

      streamRef.current = mediaStream;

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      console.error("Camera error:", err);
      setError("Failed to access camera. Please allow camera permissions.");
      setCameraState("error");
    }
  }, []);

  // Stop camera
  const stopCamera = useCallback(() => {
    if (detectionIntervalRef.current) {
      clearInterval(detectionIntervalRef.current);
      detectionIntervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, [startCamera, stopCamera]);

  const handleVideoReady = () => {
    setCameraState("ready");
  };

  // Calculate brightness
  const calculateBrightness = useCallback((imageData) => {
    const data = imageData.data;
    let total = 0;
    const count = data.length / 4;
    for (let i = 0; i < data.length; i += 4) {
      total += 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    }
    return total / count;
  }, []);

  // Calculate sharpness using Laplacian variance
  const calculateSharpness = useCallback((imageData, width, height) => {
    const data = imageData.data;
    const gray = new Float32Array(width * height);

    for (let i = 0; i < width * height; i++) {
      gray[i] =
        0.299 * data[i * 4] + 0.587 * data[i * 4 + 1] + 0.114 * data[i * 4 + 2];
    }

    let sum = 0;
    let count = 0;
    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        const idx = y * width + x;
        const lap =
          gray[idx - width] +
          gray[idx + width] +
          gray[idx - 1] +
          gray[idx + 1] -
          4 * gray[idx];
        sum += Math.abs(lap);
        count++;
      }
    }
    return sum / count;
  }, []);

  // Check if current pose matches target
  const checkPoseMatch = useCallback((yaw, targetYaw, tolerance) => {
    return Math.abs(yaw - targetYaw) <= tolerance;
  }, []);

  // Main detection and quality check loop
  useEffect(() => {
    if (cameraState !== "ready" || !modelsLoaded || capturedImage) {
      return;
    }

    const detectAndAnalyze = async () => {
      if (!videoRef.current || !analysisCanvasRef.current) return;

      const video = videoRef.current;
      if (video.readyState < 2) return;

      try {
        const faceResult = await faceDetectionService.detectFaceWithLandmarks(
          video
        );

        if (!faceResult.detected) {
          setDetectedFace(null);
          setFaceData(null);
          faceDataRef.current = null;
          setQualityStable(false);
          stabilityStartRef.current = null;
          setPoseMatched(false);

          setQualityChecks((prev) => ({
            ...prev,
            faceDetected: {
              passed: false,
              message: faceResult.multipleFaces
                ? "Multiple faces detected"
                : "No face detected",
            },
          }));
          return;
        }

        const { landmarks, boundingBox, pose } = faceResult;

        // Smooth pose with EMA
        let smoothedPose = pose;
        if (poseEmaRef.current) {
          const alpha = POSE_SMOOTHING.EMA_ALPHA;
          smoothedPose = {
            yaw: alpha * pose.yaw + (1 - alpha) * poseEmaRef.current.yaw,
            pitch: alpha * pose.pitch + (1 - alpha) * poseEmaRef.current.pitch,
            roll: alpha * pose.roll + (1 - alpha) * poseEmaRef.current.roll,
          };
        }
        poseEmaRef.current = smoothedPose;

        setDetectedFace(boundingBox);
        const newFaceData = { landmarks, boundingBox, pose: smoothedPose };
        setFaceData(newFaceData);
        faceDataRef.current = newFaceData;

        // Analyze image quality
        const canvas = analysisCanvasRef.current;
        const ctx = canvas.getContext("2d", { willReadFrequently: true });
        const width = video.videoWidth || 640;
        const height = video.videoHeight || 480;
        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(video, 0, 0, width, height);

        const imageData = ctx.getImageData(0, 0, width, height);
        const brightness = calculateBrightness(imageData);
        const sharpness = calculateSharpness(imageData, width, height);

        const faceSizeRatio =
          (boundingBox.width * boundingBox.height) / (width * height);

        // Check if pose matches current target
        const isPoseMatched = checkPoseMatch(
          smoothedPose.yaw,
          currentPose.targetYaw,
          currentPose.yawTolerance
        );
        const pitchOk =
          Math.abs(smoothedPose.pitch) <= QUALITY_THRESHOLDS.PITCH_MAX;
        const rollOk =
          Math.abs(smoothedPose.roll) <= QUALITY_THRESHOLDS.ROLL_MAX;
        const posePassed = isPoseMatched && pitchOk && rollOk;

        setPoseMatched(posePassed);

        // Draw landmarks on overlay canvas
        if (landmarksCanvasRef.current && videoRef.current) {
          drawLandmarks(
            landmarksCanvasRef.current,
            landmarks,
            videoRef.current,
            smoothedPose,
            currentPose
          );
        }

        // Update quality checks
        const newChecks = {
          faceDetected: {
            passed: true,
            message: "Face detected ✓",
          },
          faceSize: {
            passed:
              faceSizeRatio >= QUALITY_THRESHOLDS.FACE_SIZE_MIN &&
              faceSizeRatio <= QUALITY_THRESHOLDS.FACE_SIZE_MAX,
            value: Math.round(faceSizeRatio * 100),
            message:
              faceSizeRatio < QUALITY_THRESHOLDS.FACE_SIZE_MIN
                ? "Move closer"
                : faceSizeRatio > QUALITY_THRESHOLDS.FACE_SIZE_MAX
                ? "Move back"
                : "Good distance ✓",
          },
          pose: {
            passed: posePassed,
            message: posePassed
              ? `${currentPose.label} ✓`
              : `${currentPose.label} (yaw: ${Math.round(
                  smoothedPose.yaw
                )}°, target: ${currentPose.targetYaw}°)`,
          },
          brightness: {
            passed:
              brightness >= QUALITY_THRESHOLDS.BRIGHTNESS_MIN &&
              brightness <= QUALITY_THRESHOLDS.BRIGHTNESS_MAX,
            value: Math.round(brightness),
            message:
              brightness < QUALITY_THRESHOLDS.BRIGHTNESS_MIN
                ? "Too dark"
                : brightness > QUALITY_THRESHOLDS.BRIGHTNESS_MAX
                ? "Too bright"
                : "Good lighting ✓",
          },
          sharpness: {
            passed: sharpness >= QUALITY_THRESHOLDS.SHARPNESS_MIN,
            value: Math.round(sharpness * 10) / 10,
            message:
              sharpness < QUALITY_THRESHOLDS.SHARPNESS_MIN
                ? "Hold steady"
                : "Good focus ✓",
          },
        };

        setQualityChecks(newChecks);

        const passed = Object.values(newChecks).filter((c) => c.passed).length;
        setPassedCount(passed);
        const allPassed = passed === 5;
        setAllChecksPassed(allPassed);

        // Check stability for auto-capture
        if (allPassed) {
          const now = Date.now();
          if (stabilityStartRef.current === null) {
            stabilityStartRef.current = now;
          } else if (
            now - stabilityStartRef.current >=
            AUTO_CAPTURE.STABILITY_DURATION
          ) {
            setQualityStable(true);
            if (
              autoCaptureEnabled &&
              now - lastCaptureTimeRef.current >= AUTO_CAPTURE.COOLDOWN
            ) {
              handleAutoCapture();
            }
          }
        } else {
          stabilityStartRef.current = null;
          setQualityStable(false);
        }
      } catch (err) {
        console.error("Detection error:", err);
      }
    };

    detectionIntervalRef.current = setInterval(detectAndAnalyze, 125);

    return () => {
      if (detectionIntervalRef.current) {
        clearInterval(detectionIntervalRef.current);
      }
    };
  }, [
    cameraState,
    modelsLoaded,
    capturedImage,
    calculateBrightness,
    calculateSharpness,
    checkPoseMatch,
    currentPose,
    autoCaptureEnabled,
  ]);

  // Crop face from full frame
  const cropFace = (video, boundingBox) => {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    const x = boundingBox.x;
    const y = boundingBox.y;
    const width = boundingBox.width;
    const height = boundingBox.height;

    const padding = Math.max(width, height) * 0.2;
    const cropX = Math.max(0, x - padding);
    const cropY = Math.max(0, y - padding);
    const cropWidth = Math.min(video.videoWidth - cropX, width + padding * 2);
    const cropHeight = Math.min(
      video.videoHeight - cropY,
      height + padding * 2
    );

    // FaceNet512 expects 160x160 input
    canvas.width = 160;
    canvas.height = 160;

    ctx.drawImage(video, cropX, cropY, cropWidth, cropHeight, 0, 0, 160, 160);

    return canvas.toDataURL("image/jpeg", 0.9);
  };

  // Capture a single frame with fresh detection
  const captureSingleFrame = async () => {
    const video = videoRef.current;
    if (!video) throw new Error("Video not available");

    // Do fresh detection
    const faceResult = await faceDetectionService.detectFaceWithLandmarks(
      video
    );

    if (!faceResult.detected || !faceResult.boundingBox) {
      // Fallback to ref
      if (!faceDataRef.current?.boundingBox) {
        throw new Error("No face detected");
      }
      return cropFace(video, faceDataRef.current.boundingBox);
    }

    return cropFace(video, faceResult.boundingBox);
  };

  // Burst capture - capture multiple frames and select best
  const captureBurst = async () => {
    const frames = [];
    const video = videoRef.current;

    for (let i = 0; i < AUTO_CAPTURE.BURST_COUNT; i++) {
      try {
        const faceCrop = await captureSingleFrame();

        // Analyze quality
        const tempCanvas = document.createElement("canvas");
        tempCanvas.width = 160;
        tempCanvas.height = 160;
        const tempCtx = tempCanvas.getContext("2d");
        const tempImg = new Image();

        await new Promise((resolve, reject) => {
          tempImg.onload = () => {
            tempCtx.drawImage(tempImg, 0, 0);
            const imageData = tempCtx.getImageData(0, 0, 160, 160);
            const brightness = calculateBrightness(imageData);
            const sharpness = calculateSharpness(imageData, 160, 160);

            const qualityScore =
              (brightness >= QUALITY_THRESHOLDS.BRIGHTNESS_MIN &&
              brightness <= QUALITY_THRESHOLDS.BRIGHTNESS_MAX
                ? 1
                : 0) *
                0.3 +
              (sharpness >= QUALITY_THRESHOLDS.SHARPNESS_MIN ? 1 : 0) * 0.7;

            frames.push({ dataUrl: faceCrop, qualityScore, sharpness });
            resolve();
          };
          tempImg.onerror = reject;
          tempImg.src = faceCrop;
        });

        if (i < AUTO_CAPTURE.BURST_COUNT - 1) {
          await new Promise((resolve) =>
            setTimeout(resolve, AUTO_CAPTURE.BURST_INTERVAL)
          );
        }
      } catch (err) {
        console.warn("Burst frame failed:", err);
      }
    }

    if (frames.length === 0) {
      throw new Error("Failed to capture any frames");
    }

    frames.sort((a, b) => b.qualityScore - a.qualityScore);
    return frames[0].dataUrl;
  };

  // Auto-capture handler
  const handleAutoCapture = async () => {
    if (isCapturing) return;

    setIsCapturing(true);
    lastCaptureTimeRef.current = Date.now();
    setAutoCaptureEnabled(false);

    try {
      const bestFrame = await captureBurst();

      if (isMultiAngle) {
        // Multi-angle: store and move to next pose
        const newCapturedImages = [...capturedImages, bestFrame];
        setCapturedImages(newCapturedImages);

        if (currentPoseIndex < CAPTURE_POSES.length - 1) {
          // Move to next pose
          setCurrentPoseIndex(currentPoseIndex + 1);
          stabilityStartRef.current = null;
          setQualityStable(false);
          setPoseMatched(false);
          setAutoCaptureEnabled(true);
        } else {
          // All poses captured - send to parent
          setCapturedImage(bestFrame); // Show last captured
          stopCamera();

          // Convert all to files
          const files = await Promise.all(
            newCapturedImages.map(async (dataUrl, idx) => {
              const response = await fetch(dataUrl);
              const blob = await response.blob();
              return new File([blob], `face_${CAPTURE_POSES[idx].id}.jpg`, {
                type: "image/jpeg",
              });
            })
          );

          if (onMultiCapture) {
            onMultiCapture(files);
          } else if (onCapture) {
            // Fallback: send first image
            onCapture(files[0]);
          }
        }
      } else {
        // Single capture mode (attendance)
        setCapturedImage(bestFrame);
        stopCamera();

        const response = await fetch(bestFrame);
        const blob = await response.blob();
        const file = new File([blob], "face.jpg", { type: "image/jpeg" });
        if (onCapture) {
          onCapture(file);
        }
      }
    } catch (err) {
      console.error("Auto-capture error:", err);
      setError("Failed to capture. Please try again.");
      setAutoCaptureEnabled(true);
    } finally {
      setIsCapturing(false);
    }
  };

  // Manual capture handler
  const handleManualCapture = async () => {
    if (isCapturing) return;

    setIsCapturing(true);
    lastCaptureTimeRef.current = Date.now();

    try {
      const bestFrame = await captureBurst();

      if (isMultiAngle) {
        const newCapturedImages = [...capturedImages, bestFrame];
        setCapturedImages(newCapturedImages);

        if (currentPoseIndex < CAPTURE_POSES.length - 1) {
          setCurrentPoseIndex(currentPoseIndex + 1);
          stabilityStartRef.current = null;
          setQualityStable(false);
          setPoseMatched(false);
        } else {
          setCapturedImage(bestFrame);
          stopCamera();

          const files = await Promise.all(
            newCapturedImages.map(async (dataUrl, idx) => {
              const response = await fetch(dataUrl);
              const blob = await response.blob();
              return new File([blob], `face_${CAPTURE_POSES[idx].id}.jpg`, {
                type: "image/jpeg",
              });
            })
          );

          if (onMultiCapture) {
            onMultiCapture(files);
          } else if (onCapture) {
            onCapture(files[0]);
          }
        }
      } else {
        setCapturedImage(bestFrame);
        stopCamera();

        const response = await fetch(bestFrame);
        const blob = await response.blob();
        const file = new File([blob], "face.jpg", { type: "image/jpeg" });
        if (onCapture) {
          onCapture(file);
        }
      }
    } catch (err) {
      console.error("Capture error:", err);
      setError("Failed to capture. Please try again.");
    } finally {
      setIsCapturing(false);
    }
  };

  // Handle retake
  const handleRetake = () => {
    setCapturedImage(null);
    setCapturedImages([]);
    setCurrentPoseIndex(0);
    setError(null);
    setQualityStable(false);
    setPoseMatched(false);
    stabilityStartRef.current = null;
    poseEmaRef.current = null;
    setAutoCaptureEnabled(true);
    startCamera();
  };

  // Handle cancel
  const handleCancel = () => {
    stopCamera();
    if (onCancel) {
      onCancel();
    }
  };

  // Calculate ring progress
  const ringProgress = (passedCount / 5) * 100;

  const getRingColor = () => {
    if (passedCount === 5) return "#22c55e";
    if (passedCount >= 4) return "#eab308";
    if (passedCount >= 3) return "#f97316";
    return "#3b82f6";
  };

  if (cameraState === "error") {
    return (
      <div className={styles.container}>
        <div className={styles.errorContainer}>
          <div className={styles.errorIcon}>⚠️</div>
          <p className={styles.errorMessage}>{error}</p>
          <button
            className={styles.retryButton}
            onClick={() => {
              stopCamera();
              startCamera();
            }}
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.captureArea}>
        <div className={styles.videoWrapper}>
          {capturedImage ? (
            <img
              src={capturedImage}
              alt="Captured"
              className={styles.capturedImage}
            />
          ) : (
            <>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className={styles.video}
                onLoadedMetadata={handleVideoReady}
              />

              {/* Face Box */}
              {detectedFace && videoRef.current && (
                <div
                  className={`${styles.faceBox} ${
                    allChecksPassed && qualityStable ? styles.faceBoxReady : ""
                  }`}
                  style={{
                    left: `${
                      (1 -
                        (detectedFace.x + detectedFace.width) /
                          videoRef.current.videoWidth) *
                      100
                    }%`,
                    top: `${
                      (detectedFace.y / videoRef.current.videoHeight) * 100
                    }%`,
                    width: `${
                      (detectedFace.width / videoRef.current.videoWidth) * 100
                    }%`,
                    height: `${
                      (detectedFace.height / videoRef.current.videoHeight) * 100
                    }%`,
                  }}
                />
              )}

              {/* Landmarks Overlay Canvas */}
              {faceData && faceData.landmarks && videoRef.current && (
                <canvas
                  ref={landmarksCanvasRef}
                  className={styles.landmarksCanvas}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    pointerEvents: "none",
                    transform: "scaleX(-1)", // Mirror to match video
                  }}
                />
              )}

              {/* Progress Ring */}
              <div className={styles.ringOverlay}>
                <svg viewBox="0 0 100 100" className={styles.progressRingSvg}>
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="rgba(255,255,255,0.2)"
                    strokeWidth="3"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke={getRingColor()}
                    strokeWidth="3"
                    strokeDasharray={`${282.7 * (ringProgress / 100)} 282.7`}
                    strokeLinecap="round"
                    transform="rotate(-90 50 50)"
                    className={styles.progressCircle}
                  />
                </svg>
                <div className={styles.progressText}>
                  <span className={styles.progressNumber}>{passedCount}</span>
                  <span className={styles.progressLabel}>/5</span>
                </div>
              </div>

              {/* Loading */}
              {(cameraState === "initializing" || !modelsLoaded) && (
                <div className={styles.loadingOverlay}>
                  <div className={styles.spinner}></div>
                  <p>
                    {!modelsLoaded
                      ? "Loading face detection..."
                      : "Starting camera..."}
                  </p>
                </div>
              )}

              {/* Auto-capture indicator */}
              {qualityStable && allChecksPassed && (
                <div className={styles.autoCaptureIndicator}>
                  <span>✓ Capturing automatically...</span>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <canvas ref={canvasRef} style={{ display: "none" }} />
      <canvas ref={analysisCanvasRef} style={{ display: "none" }} />

      {/* Multi-angle Progress (for registration) */}
      {isMultiAngle &&
        !capturedImage &&
        cameraState === "ready" &&
        modelsLoaded && (
          <div className={styles.multiAngleProgress}>
            <div className={styles.poseSteps}>
              {CAPTURE_POSES.map((pose, idx) => (
                <div
                  key={pose.id}
                  className={`${styles.poseStep} ${
                    idx < currentPoseIndex
                      ? styles.poseCompleted
                      : idx === currentPoseIndex
                      ? styles.poseCurrent
                      : styles.posePending
                  }`}
                >
                  <div className={styles.poseIcon}>
                    {idx < currentPoseIndex ? "✓" : idx + 1}
                  </div>
                  <span className={styles.poseLabel}>{pose.label}</span>
                </div>
              ))}
            </div>
            <p className={styles.poseInstruction}>
              Step {currentPoseIndex + 1} of {totalPoses}:{" "}
              <strong>{currentPose.label}</strong>
            </p>
          </div>
        )}

      {/* Quality Panel */}
      {!capturedImage && cameraState === "ready" && modelsLoaded && (
        <div className={styles.qualityPanel}>
          <h3 className={styles.qualityTitle}>
            Quality Checks ({passedCount}/5)
          </h3>
          <div className={styles.qualityList}>
            <QualityItem
              check={qualityChecks.faceDetected}
              label="Face"
              icon="👤"
            />
            <QualityItem
              check={qualityChecks.faceSize}
              label="Distance"
              icon="↔️"
            />
            <QualityItem check={qualityChecks.pose} label="Pose" icon="📐" />
            <QualityItem
              check={qualityChecks.brightness}
              label="Lighting"
              icon="💡"
            />
            <QualityItem
              check={qualityChecks.sharpness}
              label="Focus"
              icon="🎯"
            />
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className={styles.instructions}>
        {capturedImage ? (
          <p>
            {isMultiAngle
              ? `All ${totalPoses} angles captured!`
              : "Image captured!"}
          </p>
        ) : !modelsLoaded ? (
          <p>Loading face detection...</p>
        ) : qualityStable && allChecksPassed ? (
          <p className={styles.readyText}>✓ Ready! Auto-capturing...</p>
        ) : allChecksPassed ? (
          <p className={styles.readyText}>✓ Hold still...</p>
        ) : (
          <p>{getInstruction(qualityChecks, currentPose)}</p>
        )}
      </div>

      {/* Buttons */}
      <div className={styles.buttonGroup}>
        {capturedImage ? (
          <>
            <button className={styles.retakeButton} onClick={handleRetake}>
              Retake
            </button>
            <button className={styles.cancelButton} onClick={handleCancel}>
              Done
            </button>
          </>
        ) : (
          <>
            <button className={styles.cancelButton} onClick={handleCancel}>
              Cancel
            </button>
            <button
              className={styles.captureButton}
              onClick={handleManualCapture}
              disabled={!allChecksPassed || isCapturing}
            >
              {isCapturing ? "Capturing..." : "Capture"}
            </button>
          </>
        )}
      </div>
    </div>
  );
};

// Quality check item component
const QualityItem = ({ check, label, icon }) => (
  <div
    className={`${styles.qualityItem} ${
      check.passed ? styles.qualityPassed : styles.qualityFailed
    }`}
  >
    <span className={styles.qualityIcon}>{icon}</span>
    <div className={styles.qualityInfo}>
      <span className={styles.qualityLabel}>{label}</span>
      <span className={styles.qualityMessage}>{check.message}</span>
    </div>
    <span className={styles.qualityStatus}>{check.passed ? "✓" : ""}</span>
  </div>
);

// Draw landmarks on canvas overlay
const drawLandmarks = (canvas, landmarks, video, pose, currentPose) => {
  if (!canvas || !landmarks || !video) return;

  const ctx = canvas.getContext("2d");
  const width = video.videoWidth;
  const height = video.videoHeight;

  // Set canvas size to match video
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }

  // Clear previous frame
  ctx.clearRect(0, 0, width, height);

  // Draw key landmarks
  const keyLandmarks = [
    { idx: 33, name: "leftEye", color: "#00ff00" },
    { idx: 263, name: "rightEye", color: "#00ff00" },
    { idx: 4, name: "nose", color: "#ff0000" },
    { idx: 10, name: "forehead", color: "#0000ff" },
    { idx: 152, name: "chin", color: "#0000ff" },
    { idx: 234, name: "leftCheek", color: "#ffff00" },
    { idx: 454, name: "rightCheek", color: "#ffff00" },
  ];

  keyLandmarks.forEach(({ idx, color }) => {
    const landmark = landmarks[idx];
    if (landmark) {
      const x = landmark.x * width;
      const y = landmark.y * height;

      // Draw point
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, 2 * Math.PI);
      ctx.fill();

      // Draw small circle outline
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.stroke();
    }
  });

  // Draw connecting lines for face outline (simplified)
  ctx.strokeStyle = "rgba(0, 255, 255, 0.3)";
  ctx.lineWidth = 1;

  // Draw eye line
  if (landmarks[33] && landmarks[263]) {
    ctx.beginPath();
    ctx.moveTo(landmarks[33].x * width, landmarks[33].y * height);
    ctx.lineTo(landmarks[263].x * width, landmarks[263].y * height);
    ctx.stroke();
  }

  // Draw yaw indicator line (nose to face center)
  if (pose && landmarks[4] && landmarks[234] && landmarks[454]) {
    const nose = landmarks[4];
    const leftCheek = landmarks[234];
    const rightCheek = landmarks[454];
    const faceCenterX = ((leftCheek.x + rightCheek.x) / 2) * width;
    const faceCenterY = ((leftCheek.y + rightCheek.y) / 2) * height;
    const noseX = nose.x * width;
    const noseY = nose.y * height;

    // Draw line from face center to nose (current yaw)
    // Color: green if close to target, magenta if left, cyan if right
    const yawDiff = Math.abs(pose.yaw - (currentPose?.targetYaw || 0));
    let lineColor = "#00ff00"; // green = good
    if (pose.yaw > 15) lineColor = "#ff00ff"; // magenta = too left
    if (pose.yaw < -15) lineColor = "#00ffff"; // cyan = too right

    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(faceCenterX, faceCenterY);
    ctx.lineTo(noseX, noseY);
    ctx.stroke();

    // Draw target direction (dashed yellow line)
    if (currentPose) {
      const targetYaw = currentPose.targetYaw;
      const angle = (targetYaw * Math.PI) / 180;
      const lineLength = 60;
      ctx.strokeStyle = "rgba(255, 255, 0, 0.6)";
      ctx.lineWidth = 2;
      ctx.setLineDash([8, 4]);
      ctx.beginPath();
      ctx.moveTo(faceCenterX, faceCenterY);
      ctx.lineTo(
        faceCenterX + Math.sin(angle) * lineLength,
        faceCenterY + Math.cos(angle) * lineLength
      );
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }
};

// Get instruction based on quality checks
const getInstruction = (checks, currentPose) => {
  if (!checks.faceDetected.passed) return checks.faceDetected.message;
  if (!checks.faceSize.passed) return checks.faceSize.message;
  if (!checks.pose.passed) return currentPose.label;
  if (!checks.brightness.passed) return checks.brightness.message;
  if (!checks.sharpness.passed) return checks.sharpness.message;
  return "Checking...";
};

export default FaceCapture;
