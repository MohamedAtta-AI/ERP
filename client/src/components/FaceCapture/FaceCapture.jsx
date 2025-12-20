import React, { useEffect, useRef, useState, useCallback } from "react";
import { faceDetectionService } from "../../services/faceDetectionService";
import styles from "./FaceCapture.module.css";

const QUALITY_THRESHOLDS = {
  BRIGHTNESS_MIN: 40,
  BRIGHTNESS_MAX: 220,
  SHARPNESS_MIN: 3,
  FACE_SIZE_MIN: 0.02, // 2% of frame
  FACE_SIZE_MAX: 0.65, // 65% of frame
};

const FaceCapture = ({
  onCapture,
  onCancel,
  requiresLiveness = false,
  mode = "registration",
}) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const analysisCanvasRef = useRef(null);
  const streamRef = useRef(null);
  const detectionIntervalRef = useRef(null);

  const [cameraState, setCameraState] = useState("initializing");
  const [error, setError] = useState(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [countdown, setCountdown] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [modelsLoaded, setModelsLoaded] = useState(false);

  // Detection results
  const [detectedFace, setDetectedFace] = useState(null);
  const [faceCount, setFaceCount] = useState(0);

  // Quality check states
  const [qualityChecks, setQualityChecks] = useState({
    faceDetected: { passed: false, message: "Loading..." },
    faceSize: { passed: false, value: 0, message: "Waiting..." },
    brightness: { passed: false, value: 0, message: "Checking..." },
    sharpness: { passed: false, value: 0, message: "Checking..." },
  });
  const [passedCount, setPassedCount] = useState(0);
  const [allChecksPassed, setAllChecksPassed] = useState(false);

  // Liveness state
  const [livenessComplete, setLivenessComplete] = useState(!requiresLiveness);
  const [livenessProgress, setLivenessProgress] = useState(0);

  // Check if models are already loaded (preloaded by service)
  useEffect(() => {
    const checkModels = async () => {
      try {
        // Ensure models are loaded (will use preloaded if available)
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
    // Avoid reopening if stream is already active
    if (streamRef.current) {
      return;
    }

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
      setError(
        err.name === "NotAllowedError"
          ? "Camera access denied. Please allow camera access."
          : "Failed to access camera."
      );
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

  // Calculate sharpness
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

  // Detection loop
  useEffect(() => {
    if (cameraState !== "ready" || !modelsLoaded || capturedImage) {
      return;
    }

    const detectFaces = async () => {
      if (!videoRef.current || !analysisCanvasRef.current) return;

      const video = videoRef.current;
      if (video.readyState < 2) return;

      // Detect faces using preloaded service
      try {
        const detections = await faceDetectionService.detectFaces(video);

        setFaceCount(detections.length);

        if (detections.length === 1) {
          const box = detections[0].box;
          setDetectedFace({
            x: box.x,
            y: box.y,
            width: box.width,
            height: box.height,
          });
        } else {
          setDetectedFace(null);
        }

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

        // Calculate face size ratio
        const hasFace = detections.length === 1;
        const multipleFaces = detections.length > 1;
        let faceSizeRatio = 0;

        if (hasFace && detections[0]) {
          const box = detections[0].box;
          faceSizeRatio = (box.width * box.height) / (width * height);
        }

        // Update quality checks
        const newChecks = {
          faceDetected: {
            passed: hasFace,
            message: multipleFaces
              ? "Multiple faces - one person only"
              : hasFace
              ? "Face detected ✓"
              : "No face detected",
          },
          faceSize: {
            passed:
              hasFace &&
              faceSizeRatio >= QUALITY_THRESHOLDS.FACE_SIZE_MIN &&
              faceSizeRatio <= QUALITY_THRESHOLDS.FACE_SIZE_MAX,
            value: Math.round(faceSizeRatio * 100),
            message: !hasFace
              ? "Waiting for face..."
              : faceSizeRatio < QUALITY_THRESHOLDS.FACE_SIZE_MIN
              ? "Move closer"
              : faceSizeRatio > QUALITY_THRESHOLDS.FACE_SIZE_MAX
              ? "Move back"
              : "Good distance ✓",
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
        setAllChecksPassed(passed === 4);

        // Liveness
        if (requiresLiveness && passed === 4 && !livenessComplete) {
          setLivenessProgress((prev) => {
            const next = prev + 4;
            if (next >= 100) {
              setLivenessComplete(true);
              return 100;
            }
            return next;
          });
        } else if (passed < 4 && requiresLiveness) {
          setLivenessProgress((prev) => Math.max(0, prev - 8));
        }
      } catch (err) {
        console.error("Detection error:", err);
      }
    };

    // Run detection every 200ms
    detectionIntervalRef.current = setInterval(detectFaces, 200);

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
    requiresLiveness,
    livenessComplete,
  ]);

  // Capture
  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return null;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.9);
  };

  const handleCapture = async () => {
    if (isCapturing) return;
    setIsCapturing(true);

    // for (let i = 3; i > 0; i--) {
    //   setCountdown(i);
    //   await new Promise((r) => setTimeout(r, 1000));
    // }
    // setCountdown(null);

    const imageDataUrl = captureFrame();
    if (!imageDataUrl) {
      setError("Failed to capture.");
      setIsCapturing(false);
      return;
    }

    setCapturedImage(imageDataUrl);
    stopCamera();

    try {
      const response = await fetch(imageDataUrl);
      const blob = await response.blob();
      const file = new File([blob], "face.jpg", { type: "image/jpeg" });
      if (onCapture) onCapture(file);
    } catch (err) {
      setError("Failed to process image.");
    }
    setIsCapturing(false);
  };

  const handleRetake = () => {
    setCapturedImage(null);
    setError(null);
    setLivenessProgress(0);
    setLivenessComplete(!requiresLiveness);
    setDetectedFace(null);
    setFaceCount(0);
    setPassedCount(0);
    startCamera();
  };

  const ringProgress = requiresLiveness
    ? livenessProgress
    : (passedCount / 4) * 100;
  const getRingColor = () => {
    if (allChecksPassed) return "#22c55e";
    if (passedCount >= 3) return "#eab308";
    if (passedCount >= 2) return "#f97316";
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
                    allChecksPassed ? styles.faceBoxReady : ""
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
                  <span className={styles.progressLabel}>/4</span>
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

              {/* Countdown */}
              {/* {countdown && (
                <div className={styles.countdownOverlay}>
                  <span className={styles.countdownNumber}>{countdown}</span>
                </div>
              )} */}
            </>
          )}
        </div>
      </div>

      <canvas ref={canvasRef} style={{ display: "none" }} />
      <canvas ref={analysisCanvasRef} style={{ display: "none" }} />

      {/* Quality Panel */}
      {!capturedImage && cameraState === "ready" && modelsLoaded && (
        <div className={styles.qualityPanel}>
          <h3 className={styles.qualityTitle}>
            Quality Checks ({passedCount}/4)
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

          {requiresLiveness && (
            <div className={styles.livenessSection}>
              <div className={styles.livenessHeader}>
                <span>Liveness</span>
                <span>{livenessProgress}%</span>
              </div>
              <div className={styles.livenessBar}>
                <div
                  className={styles.livenessProgress}
                  style={{ width: `${livenessProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      <div className={styles.instructions}>
        {capturedImage ? (
          <p>Image captured!</p>
        ) : !modelsLoaded ? (
          <p>Loading face detection...</p>
        ) : allChecksPassed && (!requiresLiveness || livenessComplete) ? (
          <p className={styles.readyText}>✓ Ready to capture!</p>
        ) : (
          <p>{getInstruction(qualityChecks)}</p>
        )}
      </div>

      {/* Buttons */}
      <div className={styles.actions}>
        {capturedImage ? (
          <button className={styles.retakeButton} onClick={handleRetake}>
            Retake
          </button>
        ) : (
          <>
            {onCancel && (
              <button
                className={styles.cancelButton}
                onClick={() => {
                  // Ensure camera and streams are stopped when user cancels
                  stopCamera();
                  onCancel();
                }}
              >
                Cancel
              </button>
            )}
            <button
              className={styles.captureButton}
              onClick={handleCapture}
              disabled={
                isCapturing ||
                cameraState !== "ready" ||
                !modelsLoaded ||
                !allChecksPassed ||
                (requiresLiveness && !livenessComplete)
              }
            >
              {isCapturing ? "Capturing..." : "Capture"}
            </button>
          </>
        )}
      </div>
    </div>
  );
};

const QualityItem = ({ check, label, icon }) => (
  <div
    className={`${styles.qualityItem} ${
      check.passed ? styles.passed : styles.failed
    }`}
  >
    <span className={styles.qualityIcon}>{icon}</span>
    <div className={styles.qualityInfo}>
      <span className={styles.qualityLabel}>{label}</span>
      <span className={styles.qualityMessage}>{check.message}</span>
    </div>
    <span className={styles.qualityStatus}>{check.passed ? "✓" : "○"}</span>
  </div>
);

const getInstruction = (checks) => {
  if (!checks.faceDetected.passed) return "Look at the camera";
  if (!checks.faceSize.passed) return checks.faceSize.message;
  if (!checks.brightness.passed) return checks.brightness.message;
  if (!checks.sharpness.passed) return checks.sharpness.message;
  return "Checking...";
};

export default FaceCapture;
