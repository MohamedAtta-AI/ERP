"""Face recognition service using FaceNet512 from DeepFace."""
import numpy as np
from typing import Optional, Tuple
from deepface import DeepFace


class FaceRecognitionService:
    """Service for face recognition using FaceNet512 model from DeepFace."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize face recognition service.
        
        Args:
            model_path: Not used for DeepFace (kept for compatibility)
        """
        self.model_name = "Facenet512"
        self.embedding_size = 512
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization - DeepFace models load on first use."""
        if not self._initialized:
            try:
                # DeepFace will auto-download models on first use
                self._initialized = True
                print(f"[FaceRecognition] Using DeepFace model: {self.model_name}")
            except Exception as e:
                print(f"[FaceRecognition] Warning: DeepFace initialization issue: {e}")
                self._initialized = True  # Continue anyway
    
    def generate_embedding(
        self, 
        image: np.ndarray, 
        check_anti_spoof: bool = True
    ) -> Tuple[np.ndarray, Optional[dict]]:
        """
        Generate 512-dimensional face embedding using FaceNet512.
        
        Args:
            image: Face image as numpy array (RGB format, 160x160 recommended)
            check_anti_spoof: If True, perform anti-spoofing check and return result
            
        Returns:
            Tuple of (embedding, anti_spoof_result)
            - embedding: 512-dimensional normalized embedding vector
            - anti_spoof_result: Dict with 'is_real' and 'antispoof_score' if check_anti_spoof=True, else None
        """
        self._ensure_initialized()
        
        if image is None or image.size == 0:
            raise ValueError("Empty image provided for embedding generation")
        
        try:
            import cv2
            import tempfile
            import os
            
            # Ensure image is in correct format (RGB, uint8)
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
            
            # Convert RGB to BGR for OpenCV (if needed for saving)
            if len(image.shape) == 3 and image.shape[2] == 3:
                # Assume RGB, convert to BGR for cv2.imwrite
                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            else:
                image_bgr = image
            
            # Save to temporary file for DeepFace
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                cv2.imwrite(tmp_path, image_bgr)
            
            try:
                anti_spoof_result = None
                
                # If anti-spoofing is enabled, check it first using extract_faces
                if check_anti_spoof:
                    face_objs = DeepFace.extract_faces(
                        img_path=tmp_path,
                        detector_backend="skip",  # Skip detection - use entire image as face
                        enforce_detection=False,
                        align=False,
                        anti_spoofing=True,  # Enable anti-spoofing
                    )
                    
                    if not face_objs or len(face_objs) == 0:
                        raise ValueError("No face detected for anti-spoofing check")
                    
                    face_obj = face_objs[0]
                    is_real = face_obj.get("is_real", True)
                    antispoof_score = face_obj.get("antispoof_score", 1.0)
                    
                    anti_spoof_result = {
                        "is_real": is_real,
                        "antispoof_score": float(antispoof_score),
                    }
                    
                    print(
                        f"[FaceRecognition] Anti-spoof check: is_real={is_real}, "
                        f"score={antispoof_score:.3f}"
                    )
                    
                    # If spoof detected, raise error before generating embedding
                    if not is_real:
                        raise ValueError(
                            f"Anti-spoofing failed: detected as fake (score={antispoof_score:.3f})"
                        )
                
                # Generate embedding using represent (without anti_spoofing to avoid duplicate check)
                embedding_objs = DeepFace.represent(
                    img_path=tmp_path,
                    model_name=self.model_name,
                    detector_backend="skip",  # Skip detection - use entire image as face
                    enforce_detection=False,  # Don't fail if face not detected
                    align=False,  # Already aligned
                    anti_spoofing=False,  # Already checked above if needed
                )
                
                if not embedding_objs or len(embedding_objs) == 0:
                    raise ValueError("No embedding generated from image")
                
                # Get the first embedding (should be only one for cropped face)
                embedding = np.array(embedding_objs[0]["embedding"], dtype=np.float32)
                
                # Normalize embedding (L2 normalization)
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                
                print(
                    f"[FaceRecognition] Generated {self.model_name} embedding: "
                    f"shape={embedding.shape}, norm={np.linalg.norm(embedding):.4f}"
                )
                
                return embedding, anti_spoof_result
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            print(f"[FaceRecognition] Error generating embedding: {e}")
            raise RuntimeError(f"Failed to generate face embedding: {e}")
