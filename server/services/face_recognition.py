import os
import shutil

# ============================================================================
# IMPORTANT: Configure TensorFlow for CPU-only BEFORE importing anything else
# This must happen before any TensorFlow/Keras imports
# ============================================================================
# Force CPU-only mode - set these before ANY TensorFlow imports
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable all GPUs (use -1 instead of "")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Suppress TF info/warnings
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"  # Disable oneDNN for stability
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "false"
os.environ["TF_XLA_FLAGS"] = "--tf_xla_cpu_global_jit=false"

# Prevent TensorFlow from trying to use GPU
try:
    import tensorflow as tf
    # Hide all GPUs
    tf.config.set_visible_devices([], 'GPU')
    # Disable GPU memory growth for any GPUs that might be detected
    try:
        gpus = tf.config.list_physical_devices('GPU')
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, False)
    except (ValueError, RuntimeError):
        pass  # No GPUs available or already configured, which is fine
except ImportError:
    pass  # TensorFlow not installed yet (will be imported by DeepFace later)


def _setup_deepface_models():
    """
    Setup DeepFace to use local models from server/weights.
    
    DeepFace stores models in DEEPFACE_HOME/.deepface/weights/
    This function copies models from server/weights/ to that location.
    
    MUST be called BEFORE importing DeepFace.
    """
    # Determine server path (parent of services directory)
    server_path = os.path.join(os.path.dirname(__file__), "..")
    server_path = os.path.abspath(server_path)
    
    # Set DEEPFACE_HOME if not already set
    if not os.environ.get("DEEPFACE_HOME"):
        os.environ["DEEPFACE_HOME"] = server_path
    
    deepface_home = os.environ.get("DEEPFACE_HOME", server_path)
    
    # Create .deepface/weights directory structure
    deepface_weights = os.path.join(deepface_home, ".deepface", "weights")
    os.makedirs(deepface_weights, exist_ok=True)
    
    # Source weights directory
    source_weights = os.path.join(server_path, "weights")
    if not os.path.exists(source_weights):
        print(f"[FaceRecognition] Warning: weights directory not found at {source_weights}")
        return
    
    # Map our model files to DeepFace's expected filenames
    # DeepFace Facenet uses 'facenet_weights.h5'
    model_mappings = {
        "facenet128.h5": ["facenet_weights.h5", "facenet_keras_weights.h5"],
        "facenet_weights.h5": ["facenet_weights.h5"],
        "sface.onnx": ["sface.onnx"],
    }
    
    print(f"[FaceRecognition] Setting up models:")
    print(f"  Source: {source_weights}")
    print(f"  Destination: {deepface_weights}")
    print(f"  Files in source: {os.listdir(source_weights)}")
    
    for filename in os.listdir(source_weights):
        source_file = os.path.join(source_weights, filename)
        if not os.path.isfile(source_file):
            continue
        
        # Get file size for verification
        file_size = os.path.getsize(source_file) / (1024 * 1024)  # MB
        print(f"  Found: {filename} ({file_size:.2f} MB)")
        
        # Get the list of target names for this file
        target_names = model_mappings.get(filename, [filename])
        
        for target_name in target_names:
            dest_file = os.path.join(deepface_weights, target_name)
            
            if os.path.exists(dest_file):
                dest_size = os.path.getsize(dest_file) / (1024 * 1024)
                print(f"    -> {target_name} already exists ({dest_size:.2f} MB)")
                continue
                
            # Copy the file (symlinks can be problematic in Docker)
            try:
                shutil.copy2(source_file, dest_file)
                print(f"    -> Copied to {target_name}")
            except Exception as e:
                print(f"    -> ERROR copying to {target_name}: {e}")
    
    # Verify what's in the destination
    if os.path.exists(deepface_weights):
        print(f"  Destination now contains: {os.listdir(deepface_weights)}")


# Run setup BEFORE importing DeepFace
_setup_deepface_models()

import numpy as np
from typing import Optional, Tuple
from deepface import DeepFace

from server.config import config


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
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or config.RECOGNITION_MODEL_PATH
        self.model_name = config.RECOGNITION_MODEL_NAME
        self.embedding_size = config.EMBEDDING_SIZE
        self.similarity_threshold = config.SIMILARITY_THRESHOLD

    def generate_embedding(
        self, image: np.ndarray
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
                normalization="Facenet"
                if self.model_name == "Facenet"
                else "base",  # normalize input img
                l2_normalize=True,  # normize output embedding
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

    def compute_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
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
