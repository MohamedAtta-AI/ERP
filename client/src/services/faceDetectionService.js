/**
 * Global face detection service that preloads models once
 * and provides a singleton instance for all components.
 */
import * as faceapi from "face-api.js";

class FaceDetectionService {
  constructor() {
    this.modelsLoaded = false;
    this.loadingPromise = null;
    this.MODEL_URL = "https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model";
  }

  /**
   * Load models if not already loaded or loading
   * Returns a promise that resolves when models are ready
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
      console.log("[FaceDetection] Loading models from CDN...");
      await faceapi.nets.tinyFaceDetector.loadFromUri(this.MODEL_URL);
      this.modelsLoaded = true;
      console.log("[FaceDetection] Models loaded successfully");
      return true;
    } catch (err) {
      console.error("[FaceDetection] Failed to load models:", err);
      this.loadingPromise = null; // Allow retry
      throw err;
    }
  }

  /**
   * Detect faces in an image/video element
   */
  async detectFaces(video, options = {}) {
    if (!this.modelsLoaded) {
      await this.ensureModelsLoaded();
    }

    return faceapi.detectAllFaces(
      video,
      new faceapi.TinyFaceDetectorOptions({
        inputSize: 320,
        scoreThreshold: 0.5,
        ...options,
      })
    );
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

// Preload models immediately when module is imported
faceDetectionService.ensureModelsLoaded().catch((err) => {
  console.warn("[FaceDetection] Preload failed, will retry on first use:", err);
});

