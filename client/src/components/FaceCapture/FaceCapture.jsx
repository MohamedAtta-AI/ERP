import React, { useEffect, useRef, useState, useCallback } from "react";
import { faceDetectionService } from "../../services/faceDetectionService";
import styles from "./FaceCapture.module.css";

// Production-quality thresholds
const QUALITY_THRESHOLDS = {
  BRIGHTNESS_MIN: 60,
  BRIGHTNESS_MAX: 200,
  SHARPNESS_MIN: 1.5,
  FACE_SIZE_MIN: 0.18, // Face must be much closer for reliable recognition
  FACE_SIZE_MAX: 0.50,
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

// Target rectangle configuration (where face should be positioned)
// Values are percentages of the video dimensions
const TARGET_RECT = {
  x: 0.2,       // 20% from left
  y: 0.1,       // 10% from top
  width: 0.6,   // 60% of video width
  height: 0.8,  // 80% of video height
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
  verificationResult = null, // For attendance mode: { verified, verifying, full_name, person_id } from parent
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
  const [faceInsideTarget, setFaceInsideTarget] = useState(false);

  // Quality check states
  const [qualityChecks, setQualityChecks] = useState({
    faceDetected: { passed: false, message: "Loading..." },
    facePosition: { passed: false, message: "Waiting..." },
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
    let mounted = true;
    const checkModels = async () => {
      try {
        // Check if already loaded
        if (faceDetectionService.isReady()) {
          if (mounted) setModelsLoaded(true);
          return;
        }
        
        // Load models
        await faceDetectionService.ensureModelsLoaded();
        if (mounted) setModelsLoaded(true);
      } catch (err) {
        console.error("Failed to load face detection models:", err);
        // Allow camera to start, but keep modelsLoaded=false so detection doesn't run.
        if (mounted) {
          setModelsLoaded(false);
          setError(
            "Face detection failed to initialize. Please refresh the page. " +
              "If you're running the dev server, restart it after dependency changes."
          );
        }
      }
    };
    checkModels();
    return () => {
      mounted = false;
    };
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

  // Calculate brightness from face crop
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

  // Check if face bounding box is inside target rectangle
  const checkFaceInsideTarget = useCallback((boundingBox, videoWidth, videoHeight) => {
    // Target rectangle in pixels
    const targetX = TARGET_RECT.x * videoWidth;
    const targetY = TARGET_RECT.y * videoHeight;
    const targetWidth = TARGET_RECT.width * videoWidth;
    const targetHeight = TARGET_RECT.height * videoHeight;
    const targetRight = targetX + targetWidth;
    const targetBottom = targetY + targetHeight;

    // Face bounding box
    const faceLeft = boundingBox.x;
    const faceTop = boundingBox.y;
    const faceRight = faceLeft + boundingBox.width;
    const faceBottom = faceTop + boundingBox.height;

    // Check if face is completely inside target rectangle
    const isInside = (
      faceLeft >= targetX &&
      faceTop >= targetY &&
      faceRight <= targetRight &&
      faceBottom <= targetBottom
    );

    return isInside;
  }, []);

  // Main detection and quality check loop
  useEffect(() => {
    // Allow camera to show even if models aren't loaded yet
    if (cameraState !== "ready" || capturedImage) {
      return;
    }
    
    // Don't start detection until models are loaded
    if (!modelsLoaded) {
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

        if (faceResult?.error) {
          setError(
            "Face detection initialization error. Please refresh. " +
              "If running locally, restart the dev server. " +
              `(${faceResult.error})`
          );
          return;
        }

        if (!faceResult.detected) {
          setDetectedFace(null);
          setFaceData(null);
          faceDataRef.current = null;
          setQualityStable(false);
          stabilityStartRef.current = null;
          setPoseMatched(false);
          setFaceInsideTarget(false);

          setQualityChecks((prev) => ({
            ...prev,
            faceDetected: {
              passed: false,
              message: faceResult.multipleFaces
                ? "Multiple faces detected"
                : "No face detected",
            },
            facePosition: { passed: false, message: "Position face in yellow box" },
          }));
          return;
        }

        const { landmarks, boundingBox, pose } = faceResult;
        const videoWidth = video.videoWidth || 640;
        const videoHeight = video.videoHeight || 480;

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

        // Check if face is inside target rectangle
        const isInsideTarget = checkFaceInsideTarget(boundingBox, videoWidth, videoHeight);
        setFaceInsideTarget(isInsideTarget);

        // Analyze image quality - use face crop for brightness/sharpness checks
        const canvas = analysisCanvasRef.current;
        const ctx = canvas.getContext("2d", { willReadFrequently: true });
        
        // Get face crop region with padding for quality analysis
        const padding = Math.max(boundingBox.width, boundingBox.height) * 0.15;
        const cropX = Math.max(0, boundingBox.x - padding);
        const cropY = Math.max(0, boundingBox.y - padding);
        const cropWidth = Math.min(videoWidth - cropX, boundingBox.width + padding * 2);
        const cropHeight = Math.min(videoHeight - cropY, boundingBox.height + padding * 2);
        
        // Set canvas to face crop size
        const analysisSize = 160; // Use consistent size for analysis
        canvas.width = analysisSize;
        canvas.height = analysisSize;
        
        // Draw only the face crop region to canvas
        ctx.drawImage(
          video, 
          cropX, cropY, cropWidth, cropHeight,  // Source region (face)
          0, 0, analysisSize, analysisSize       // Destination (canvas)
        );

        const imageData = ctx.getImageData(0, 0, analysisSize, analysisSize);
        const brightness = calculateBrightness(imageData);
        const sharpness = calculateSharpness(imageData, analysisSize, analysisSize);

        // Calculate face size ratio relative to full video frame
        const faceSizeRatio =
          (boundingBox.width * boundingBox.height) / (videoWidth * videoHeight);

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

        // Draw landmarks and target rectangle on overlay canvas
        if (landmarksCanvasRef.current && videoRef.current) {
          drawOverlay(
            landmarksCanvasRef.current,
            landmarks,
            videoRef.current,
            smoothedPose,
            currentPose,
            isInsideTarget
          );
        }

        // Update quality checks
        const newChecks = {
          faceDetected: {
            passed: true,
            message: "Face detected ✓",
          },
          facePosition: {
            passed: isInsideTarget,
            message: isInsideTarget 
              ? "Face in position ✓" 
              : "Move face into yellow box",
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
        const allPassed = passed === 6; // Now 6 checks including face position
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
    checkFaceInsideTarget,
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
        // For attendance mode: don't show captured image, let parent handle display
        // Keep camera running - parent will remount component if needed
        const response = await fetch(bestFrame);
        const blob = await response.blob();
        const file = new File([blob], "face.jpg", { type: "image/jpeg" });
        if (onCapture) {
          onCapture(file);
        }
        // Reset for next capture attempt (parent will remount on success)
        setAutoCaptureEnabled(true);
        stabilityStartRef.current = null;
        setQualityStable(false);
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
        // Single capture mode (attendance)
        // For attendance mode: don't show captured image, let parent handle display
        const response = await fetch(bestFrame);
        const blob = await response.blob();
        const file = new File([blob], "face.jpg", { type: "image/jpeg" });
        if (onCapture) {
          onCapture(file);
        }
        // Reset for next capture attempt
        stabilityStartRef.current = null;
        setQualityStable(false);
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
    setFaceInsideTarget(false);
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
  const ringProgress = (passedCount / 6) * 100; // Now 6 checks

  const getRingColor = () => {
    if (passedCount === 6) return "#22c55e";
    if (passedCount >= 5) return "#eab308";
    if (passedCount >= 4) return "#f97316";
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

              {/* Target Rectangle Guide (Yellow) */}
              <div 
                className={`${styles.targetRect} ${faceInsideTarget ? styles.targetRectActive : ''}`}
                style={{
                  left: `${(1 - TARGET_RECT.x - TARGET_RECT.width) * 100}%`,
                  top: `${TARGET_RECT.y * 100}%`,
                  width: `${TARGET_RECT.width * 100}%`,
                  height: `${TARGET_RECT.height * 100}%`,
                }}
              />

              {/* Face Box */}
              {detectedFace && videoRef.current && (
                <div
                  className={`${styles.faceBox} ${
                    allChecksPassed && qualityStable ? styles.faceBoxReady : ""
                  } ${faceInsideTarget ? styles.faceBoxInside : ""}`}
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
                  <span className={styles.progressLabel}>/6</span>
                </div>
              </div>

              {/* Loading */}
              {cameraState === "initializing" && (
                <div className={styles.loadingOverlay}>
                  <div className={styles.spinner}></div>
                  <p>Starting camera...</p>
                </div>
              )}
              
              {cameraState === "ready" && !modelsLoaded && (
                <div className={styles.loadingOverlay}>
                  <div className={styles.spinner}></div>
                  <p>Loading face detection models...</p>
                </div>
              )}

              {/* Hold indicator during verification (attendance mode) */}
              {verificationResult?.verifying && (
                <div className={`${styles.autoCaptureIndicator} ${styles.holdIndicator}`}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ width: "18px", height: "18px" }}>
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 6v6l4 2" />
                  </svg>
                  <span>Hold still...</span>
                </div>
              )}

              {/* Auto-capture indicator */}
              {qualityStable && allChecksPassed && !verificationResult?.verified && !verificationResult?.verifying && (
                <div className={styles.autoCaptureIndicator}>
                  <span>✓ Capturing automatically...</span>
                </div>
              )}

              {/* Verification Success Overlay (attendance mode) */}
              {verificationResult?.verified && (
                <div className={`${styles.verificationSuccessOverlay} ${
                  verificationResult.action === "check-out" ? styles.verificationCheckOut : ""
                }`}>
                  <div className={styles.verificationIcon}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                      <polyline points="22 4 12 14.01 9 11.01" />
                    </svg>
                  </div>
                  <div className={styles.verificationInfo}>
                    <span className={styles.verificationName}>{verificationResult.full_name}</span>
                    <span className={styles.verificationId}>ID: {verificationResult.person_id}</span>
                    {verificationResult.action && (
                      <span className={styles.verificationAction}>
                        {verificationResult.action === "check-in" ? "✓ Checked In" : 
                         verificationResult.action === "check-out" ? "✓ Checked Out" : 
                         "Already Done Today"}
                      </span>
                    )}
                  </div>
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
            Quality Checks ({passedCount}/6)
          </h3>
          <div className={styles.qualityList}>
            <QualityItem
              check={qualityChecks.faceDetected}
              label="Face"
              icon="👤"
            />
            <QualityItem
              check={qualityChecks.facePosition}
              label="Position"
              icon="🎯"
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
              icon="🔍"
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
        ) : mode === "attendance" ? (
          /* Attendance mode: minimal buttons, auto-capture handles everything */
          !verificationResult?.verified && (
            <button className={styles.cancelButton} onClick={handleCancel}>
              Exit
            </button>
          )
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

// Quality check item component with green/red styling
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
    <span className={`${styles.qualityStatus} ${check.passed ? styles.statusPassed : styles.statusFailed}`}>
      {check.passed ? "✓" : "✗"}
    </span>
  </div>
);

// Draw overlay with target rectangle and landmarks
const drawOverlay = (canvas, landmarks, video, pose, currentPose, isInsideTarget) => {
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
  if (!checks.facePosition.passed) return "Position your face inside the yellow box";
  if (!checks.faceSize.passed) return checks.faceSize.message;
  if (!checks.pose.passed) return currentPose.label;
  if (!checks.brightness.passed) return checks.brightness.message;
  if (!checks.sharpness.passed) return checks.sharpness.message;
  return "Checking...";
};

export default FaceCapture;
