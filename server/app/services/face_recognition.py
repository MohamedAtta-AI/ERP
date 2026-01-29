import os
import shutil
import numpy as np
from typing import Optional, Tuple
from deepface import DeepFace

from server.config import config

os.environ["TF_XLA_FLAGS"] = "--tf_xla_cpu_global_jit=false"

AVAILABLE_MODELS = [
    "VGG-Face",
    "Facenet",
    "Facenet512",
    "OpenFace",
    "DeepFace",
    "DeepID",
    "ArcFace",
    "Dlib",
    "SFace",
    "GhostFaceNet",
    "Buffalo_L",
]


class FaceRecognitionService:
    def __init__(self):
        self.model_name = config.RECOGNITION_MODEL_NAME
        self.embedding_size = config.EMBEDDING_SIZE
        self.similarity_threshold = config.SIMILARITY_THRESHOLD

    def generate_embedding(self, image: np.ndarray) -> list[float]:
        if self.model_name not in AVAILABLE_MODELS:
            raise ValueError(f"Invalid model name: {self.model_name}")

        embedding_objs = DeepFace.represent(
            img_path=image,
            model_name=self.model_name,
            detector_backend="skip",
            enforce_detection=False,
            align=True,
            anti_spoofing=True,
            normalization="Facenet"
            if self.model_name == "Facenet"
            else "base",  # normalize input img
            l2_normalize=True,  # normize output embedding
        )

        if not embedding_objs or len(embedding_objs) == 0:
            raise ValueError("No embedding generated from image")

        return embedding_objs[0]["embedding"]

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two face embeddings.
        
        Args:
            embedding1: First face embedding vector
            embedding2: Second face embedding vector
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        # Ensure embeddings are normalized (they should be from generate_embedding)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)

    def is_match(self, embedding1: np.ndarray, embedding2: np.ndarray) -> bool:
        """
        Check if two face embeddings match based on the configured threshold.
        
        Args:
            embedding1: First face embedding vector
            embedding2: Second face embedding vector
            
        Returns:
            True if similarity >= threshold, False otherwise
        """
        similarity = self.compute_similarity(embedding1, embedding2)
        return similarity >= self.similarity_threshold

    def find_best_match(
        self, query_embedding: np.ndarray, candidate_embeddings: list[np.ndarray]
    ) -> Tuple[Optional[int], float]:
        """
        Find the best matching embedding from a list of candidates.
        
        Args:
            query_embedding: The embedding to match against
            candidate_embeddings: List of candidate embeddings
            
        Returns:
            Tuple of (best_match_index, similarity_score) or (None, 0.0) if no match
        """
        if not candidate_embeddings:
            return None, 0.0
            
        best_idx = None
        best_similarity = 0.0
        
        for idx, candidate in enumerate(candidate_embeddings):
            similarity = self.compute_similarity(query_embedding, candidate)
            if similarity > best_similarity:
                best_similarity = similarity
                best_idx = idx
                
        if best_similarity >= self.similarity_threshold:
            return best_idx, best_similarity
        return None, best_similarity
