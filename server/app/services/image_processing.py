"""Image processing utilities."""
import cv2
import numpy as np
from typing import Union


def process_image_for_recognition(image_data: bytes) -> np.ndarray:
    """Process image for face recognition.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Processed image as numpy array (BGR format)
    """
    # Decode image
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Failed to decode image")
    
    # Convert BGR to RGB (SFace expects RGB)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    return image_rgb


def resize_image(image: np.ndarray, target_size: tuple = (112, 112)) -> np.ndarray:
    """Resize image to target size."""
    return cv2.resize(image, target_size)


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalize image to [0, 1] range."""
    return image.astype(np.float32) / 255.0
