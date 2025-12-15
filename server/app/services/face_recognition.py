"""Face recognition service using SFace model."""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional


class FaceRecognitionService:
    """Service for face recognition using SFace model."""
    
    def __init__(self, model_path: str):
        """Initialize face recognition service."""
        self.model_path = Path(model_path)
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load SFace model."""
        # Handle relative paths from project root
        original_path = self.model_path
        if not self.model_path.is_absolute():
            from pathlib import Path
            # Go up from: server/app/services/face_recognition.py -> server/app/services -> server/app -> server -> project root
            project_root = Path(__file__).parent.parent.parent.parent
            self.model_path = (project_root / original_path).resolve()
        
        if not self.model_path.exists():
            # Don't raise error immediately - allow service to be created but model won't be loaded
            print(f"WARNING: Face recognition model not found at {self.model_path}")
            print("   Face enrollment and verification will fail until model is available.")
            print("   Please download the model or update SFACE_MODEL_PATH in config.")
            self.model = None
            return
        
        try:
            print(f"Loading face recognition model from {self.model_path}...")
            self.model = cv2.dnn.readNetFromONNX(str(self.model_path))
            print("Face recognition model loaded successfully!")
        except Exception as e:
            print(f"ERROR: Failed to load face recognition model: {e}")
            self.model = None
    
    def generate_embedding(self, image: np.ndarray) -> np.ndarray:
        """Generate 128-dimensional face embedding."""
        if self.model is None:
            raise RuntimeError(
                f"Face recognition model not loaded. "
                f"Please ensure the model file exists at {self.model_path}"
            )
        
        # Preprocess image (resize to 112x112, normalize)
        blob = cv2.dnn.blobFromImage(
            image,
            scalefactor=1.0 / 255.0,
            size=(112, 112),
            mean=(127.5, 127.5, 127.5),
            swapRB=True,
            crop=False
        )
        
        # Set input and forward pass
        self.model.setInput(blob)
        embedding = self.model.forward()
        
        # Normalize embedding
        embedding = embedding.flatten()
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding.astype(np.float32)
