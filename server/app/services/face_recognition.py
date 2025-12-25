import os
import tempfile
import cv2
import numpy as np
from typing import Optional, Tuple
from deepface import DeepFace


AVAILABLE_MODELS = [
    "VGG-Face", "Facenet", "Facenet512", "OpenFace", "DeepFace",
    "DeepID", "ArcFace", "Dlib", "SFace", "GhostFaceNet",
    "Buffalo_L",
]


class FaceRecognitionService:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model_name = "Facenet"
        self.embedding_size = 512
    
    def generate_embedding(
        self, 
        image: np.ndarray
    ) -> Tuple[np.ndarray, Optional[dict]]:
        try:
            if self.model_name not in AVAILABLE_MODELS:
                raise ValueError(f"Invalid model name: {self.model_name}")
            
            embedding_objs = DeepFace.represent(
                img_path=image,
                model_name=self.model_name,
                detector_backend="skip",
                enforce_detection=False,
                align=False,
                anti_spoofing=True,
                normalization="Facenet" if self.model_name == "Facenet" else "base", # normalize input img
                l2_normalize=True, # normize output embedding
            )
            
            if not embedding_objs or len(embedding_objs) == 0:
                raise ValueError("No embedding generated from image")
            
            # Get the first embedding and anti-spoofing result if present
            embedding_obj = embedding_objs[0]
            embedding = np.array(embedding_obj["embedding"], dtype=np.float32)
            is_real = embedding_obj.get("is_real", None)
            
            return embedding, is_real

        except Exception as e:
            print(f"[FaceRecognition] Error generating embedding: {e}")
            raise RuntimeError(f"Failed to generate face embedding: {e}")
