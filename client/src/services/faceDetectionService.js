/**
 * Global face detection service using MediaPipe Face Mesh
 * Provides face detection with landmarks for quality checks and liveness
 */
// IMPORTANT:
// `@mediapipe/face_mesh` is shipped as UMD and registers `FaceMesh` on the global object.
// Named ESM imports can fail under Vite/Rollup (and may be tree-shaken due to `sideEffects: []`).
// Import the module namespace to ensure evaluation, then fall back to globalThis.
import * as mpFaceMesh from "@mediapipe/face_mesh";

class FaceDetectionService {
  constructor() {
    this.modelsLoaded = false;
    this.loadingPromise = null;
    this.faceMesh = null;
    this.requestQueue = []; // Queue of pending requests
    this.processing = false;
    this.initError = null;
  }

  /**
   * Load MediaPipe Face Mesh model
   */
  async ensureModelsLoaded() {
    if (this.modelsLoaded) {
      return Promise.resolve();
    }

    if (this.loadingPromise) {
      return this.loadingPromise;
    }

    this.loadingPromise = this._loadModels();
    return this.loadingPromise;
  }

  async _loadModels() {
    try {
      console.log("[FaceDetection] Loading MediaPipe Face Mesh from local files...");
      const FaceMeshCtor =
        mpFaceMesh?.FaceMesh ||
        globalThis?.FaceMesh ||
        (typeof window !== "undefined" ? window.FaceMesh : undefined);

      if (typeof FaceMeshCtor !== "function") {
        const err = new TypeError(
          "MediaPipe FaceMesh constructor not found (FaceMesh is not a constructor). " +
            "This usually means the bundler didn't evaluate @mediapipe/face_mesh. " +
            "Restart the dev server after dependency changes."
        );
        this.initError = err;
        throw err;
      }

      this.faceMesh = new FaceMeshCtor({
        locateFile: (file) => {
          // Use local files from public folder for offline support
          return `/models/mediapipe/${file}`;
        },
      });

      this.faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });

      // Set up persistent callback
      this.faceMesh.onResults((results) => {
        this._handleResults(results);
      });

      // Initialize by sending a dummy image
      // MediaPipe loads models lazily on first send, so we trigger that here
      const canvas = document.createElement("canvas");
      canvas.width = 1;
      canvas.height = 1;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "black";
      ctx.fillRect(0, 0, 1, 1);
      
      try {
        this.faceMesh.send({ image: canvas });
      } catch (err) {
        console.warn("[FaceDetection] Initial send failed (may be normal):", err);
      }

      // Wait a bit for models to load, then mark as ready
      // MediaPipe loads models asynchronously, so we give it time
      await new Promise((resolve) => {
        setTimeout(() => {
          this.modelsLoaded = true;
          console.log("[FaceDetection] MediaPipe Face Mesh ready");
          resolve();
        }, 1000); // Give 1 second for models to load
      });

      return true;
    } catch (err) {
      console.error("[FaceDetection] Failed to load models:", err);
      this.loadingPromise = null;
      this.initError = err;
      // Keep modelsLoaded = false so the UI can reflect "models not ready"
      // and we don't call `.send()` on a null `faceMesh`.
      this.modelsLoaded = false;
      throw err;
    }
  }

  /**
   * Handle MediaPipe results and resolve pending requests
   */
  _handleResults(results) {
    if (this.requestQueue.length === 0) {
      return;
    }

    const { resolve, video, timeout } = this.requestQueue.shift();
    clearTimeout(timeout);

    if (
      !results.multiFaceLandmarks ||
      results.multiFaceLandmarks.length === 0
    ) {
      resolve({
        detected: false,
        landmarks: null,
        boundingBox: null,
        pose: null,
      });
      this.processing = false;
      this._processNext();
      return;
    }

    if (results.multiFaceLandmarks.length > 1) {
      resolve({
        detected: false,
        multipleFaces: true,
        landmarks: null,
        boundingBox: null,
        pose: null,
      });
      this.processing = false;
      this._processNext();
      return;
    }

    const landmarks = results.multiFaceLandmarks[0];
    const boundingBox = this._calculateBoundingBox(landmarks, video);
    const pose = this._calculatePose(landmarks);

    resolve({
      detected: true,
      landmarks: landmarks,
      boundingBox: boundingBox,
      pose: pose,
    });

    this.processing = false;
    this._processNext();
  }

  /**
   * Process next request in queue
   */
  _processNext() {
    if (this.processing || this.requestQueue.length === 0) {
      return;
    }

    if (!this.faceMesh) {
      // Fail-fast queued requests if initialization failed.
      while (this.requestQueue.length) {
        const { resolve, timeout } = this.requestQueue.shift();
        clearTimeout(timeout);
        resolve({
          detected: false,
          landmarks: null,
          boundingBox: null,
          pose: null,
          error: this.initError ? String(this.initError) : "FaceMesh not initialized",
        });
      }
      this.processing = false;
      return;
    }

    const { video } = this.requestQueue[0];
    this.processing = true;
    this.faceMesh.send({ image: video });
  }

  /**
   * Detect face with landmarks in an image/video element
   * Returns: { detected: boolean, landmarks: array, boundingBox: object, pose: object }
   */
  async detectFaceWithLandmarks(video) {
    if (!this.modelsLoaded) {
      await this.ensureModelsLoaded();
    }

    if (!this.faceMesh) {
      return {
        detected: false,
        landmarks: null,
        boundingBox: null,
        pose: null,
        error: this.initError ? String(this.initError) : "FaceMesh not initialized",
      };
    }

    return new Promise((resolve) => {
      // Use a timeout to prevent hanging
      const timeout = setTimeout(() => {
        // Remove from queue if still pending
        const index = this.requestQueue.findIndex(
          (req) => req.timeout === timeout
        );
        if (index !== -1) {
          this.requestQueue.splice(index, 1);
        }
        if (this.requestQueue.length === 0) {
          this.processing = false;
        }
        resolve({
          detected: false,
          landmarks: null,
          boundingBox: null,
          pose: null,
        });
      }, 300); // 300ms timeout

      // Add to queue
      this.requestQueue.push({ resolve, video, timeout });

      // Process if not already processing
      if (!this.processing) {
        this._processNext();
      }
    });
  }

  /**
   * Calculate bounding box from landmarks
   */
  _calculateBoundingBox(landmarks, video) {
    let minX = Infinity,
      maxX = -Infinity,
      minY = Infinity,
      maxY = -Infinity;

    landmarks.forEach((landmark) => {
      const x = landmark.x * video.videoWidth;
      const y = landmark.y * video.videoHeight;
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
    });

    const padding = 20;
    return {
      x: Math.max(0, minX - padding),
      y: Math.max(0, minY - padding),
      width: Math.min(video.videoWidth, maxX - minX + padding * 2),
      height: Math.min(video.videoHeight, maxY - minY + padding * 2),
    };
  }

  /**
   * Calculate head pose (yaw, pitch, roll) from landmarks
   * Using key facial landmarks for pose estimation
   */
  _calculatePose(landmarks) {
    // IMPORTANT:
    // MediaPipe provides normalized landmark coordinates (x,y,z).
    // A full head-pose solvePnP is overkill here; we only need a stable "frontalness" estimate.
    // The previous implementation used hard-coded denominators which produced very noisy angles.

    // Key landmark indices
    const LEFT_EYE_OUTER = 33;
    const RIGHT_EYE_OUTER = 263;
    const NOSE_TIP = 4;
    const FOREHEAD = 10;
    const CHIN = 152;
    const LEFT_CHEEK = 234;
    const RIGHT_CHEEK = 454;

    const leftEye = landmarks[LEFT_EYE_OUTER];
    const rightEye = landmarks[RIGHT_EYE_OUTER];
    const nose = landmarks[NOSE_TIP];
    const forehead = landmarks[FOREHEAD];
    const chin = landmarks[CHIN];
    const leftCheek = landmarks[LEFT_CHEEK];
    const rightCheek = landmarks[RIGHT_CHEEK];

    const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

    // Roll: slope of eye line (stable)
    const eyeDeltaY = rightEye.y - leftEye.y;
    const eyeDeltaX = rightEye.x - leftEye.x;
    const roll = Math.atan2(eyeDeltaY, eyeDeltaX) * (180 / Math.PI);

    // Yaw: compare nose horizontal offset relative to face width
    // Use eye positions for more stable reference
    const eyeCenterX = (leftEye.x + rightEye.x) / 2;
    const faceWidth = Math.max(1e-6, Math.abs(rightEye.x - leftEye.x));
    const noseOffset = nose.x - eyeCenterX;
    const yawRatio = noseOffset / (faceWidth / 2); // Normalized to [-1, 1]

    // Map ratio to degrees with better scaling
    // Positive yaw = turning left (nose moves right relative to center)
    // Negative yaw = turning right (nose moves left relative to center)
    const yaw = clamp(yawRatio * 40, -50, 50);

    // Pitch: compare nose vertical offset relative to face height
    const faceCenterY = (forehead.y + chin.y) / 2;
    const halfFaceHeight = Math.max(1e-6, Math.abs(chin.y - forehead.y) / 2);
    const pitchRatio = (nose.y - faceCenterY) / halfFaceHeight;
    // Negative pitch = looking up (nose higher); positive = looking down.
    const pitch = clamp(pitchRatio * 30, -40, 40);

    return { yaw, pitch, roll };
  }

  /**
   * Check if models are loaded
   */
  isReady() {
    return this.modelsLoaded;
  }
}

// Export singleton instance
export const faceDetectionService = new FaceDetectionService();

/**
 * Preload models immediately when module is imported.
 * This runs in the background without blocking the UI.
 */
const preloadModels = () => {
  // Start loading immediately but don't block
  faceDetectionService.ensureModelsLoaded().catch((err) => {
    console.warn("[FaceDetection] Preload failed, will retry on first use:", err);
  });
};

// Preload immediately - MediaPipe loading is async and won't block
preloadModels();

/**
 * Check if models are ready (for UI status indicators)
 */
export const areModelsReady = () => faceDetectionService.isReady();

