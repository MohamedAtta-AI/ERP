"""
Image processing utilities for pre-cropped face images.

ARCHITECTURE:
- Frontend detects face using MediaPipe Face Mesh
- Frontend crops face region (with padding) and resizes to 112x112
- Frontend sends ONLY the 112x112 face crop to backend
- Backend validates crop and generates embedding (no detection needed)

This reduces:
- Bandwidth: ~95% reduction (112x112 crop vs 640x480 full image)
- Latency: No redundant face detection on backend
- CPU: Backend only processes small face crops
"""
import cv2
import numpy as np
from typing import Tuple


def validate_face_crop(image: np.ndarray) -> bool:
    """
    Lightweight validation that received image is actually a face crop.
    
    Args:
        image: Image to validate
        
    Returns:
        True if appears to be a valid face crop
    """
    # Check dimensions (should be close to 112x112 for SFace)
    h, w = image.shape[:2]
    if w < 50 or h < 50 or w > 200 or h > 200:
        return False
    
    # Check if image has reasonable color variation (faces have variation)
    if len(image.shape) == 3:
        color_variance = np.var(image.reshape(-1, 3), axis=0).mean()
        if color_variance < 100:  # Too uniform, probably not a face
            return False
    
    return True


def process_face_crop_for_recognition(image_data: bytes) -> np.ndarray:
    """
    Process pre-cropped face image for recognition.
    Frontend sends 112x112 face crop, backend just validates and converts.
    
    Args:
        image_data: Raw image bytes (should be 112x112 face crop)
        
    Returns:
        Processed image as numpy array (RGB, 112x112)
    """
    # Decode image
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Failed to decode image")
    
    # Validate it's a reasonable face crop
    if not validate_face_crop(image):
        raise ValueError("Invalid face crop - image does not appear to be a face region")
    
    # Ensure it's 112x112 (resize if needed, though frontend should send correct size)
    if image.shape[0] != 112 or image.shape[1] != 112:
        image = cv2.resize(image, (112, 112))
    
    # Convert BGR to RGB (SFace expects RGB)
    if len(image.shape) == 3:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        # Grayscale - convert to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    
    return image_rgb


def resize_image(image: np.ndarray, target_size: tuple = (112, 112)) -> np.ndarray:
    """Resize image to target size."""
    return cv2.resize(image, target_size)


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalize image to [0, 1] range."""
    return image.astype(np.float32) / 255.0
