"""
Lightweight anti-spoofing (liveness) using DeepFace.

DeepFace provides a lightweight anti-spoofing module that can detect
if a face is real or fake (spoofed) in real-time.

Expected input:
- a pre-cropped face image (numpy array), RGB format, any size
- DeepFace will handle detection and anti-spoofing internally
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import numpy as np
import tempfile
import os
from pathlib import Path
from deepface import DeepFace


@dataclass
class AntiSpoofResult:
    is_live: bool
    live_score: float
    fake_score: float
    threshold: float
    details: Dict[str, Any]


class AntiSpoofingService:
    """
    Lightweight anti-spoofing service using DeepFace.
    
    DeepFace's anti-spoofing is optimized for real-time use and provides
    a simple boolean result indicating if the face is real or fake.
    """
    
    def __init__(self):
        """Initialize the anti-spoofing service."""
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization - DeepFace models load on first use."""
        if not self._initialized:
            # Test initialization with a dummy call
            # This will download models on first run
            try:
                # DeepFace will auto-download models on first use
                self._initialized = True
            except Exception as e:
                print(f"[ANTISPOOF] Warning: DeepFace initialization issue: {e}")
                self._initialized = True  # Continue anyway
    
    def check(self, face_image: np.ndarray) -> AntiSpoofResult:
        """
        Run anti-spoofing check on a face image.
        
        Args:
            face_image: Pre-cropped face image as numpy array (RGB format)
            
        Returns:
            AntiSpoofResult with is_live, scores, and details
        """
        self._ensure_initialized()
        
        if face_image is None or face_image.size == 0:
            return AntiSpoofResult(
                is_live=False,
                live_score=0.0,
                fake_score=1.0,
                threshold=0.5,
                details={"reason": "empty_image"},
            )
        
        try:
            # DeepFace's extract_faces with anti_spoofing=True
            # For pre-cropped faces, we need to save temporarily and use opencv detector
            # which is lightweight and works well with cropped faces
            
            # Ensure image is in correct format (RGB, uint8)
            if face_image.dtype != np.uint8:
                face_image = (face_image * 255).astype(np.uint8)
            
            # Convert RGB to BGR for OpenCV (if needed for saving)
            import cv2
            if len(face_image.shape) == 3 and face_image.shape[2] == 3:
                # Assume RGB, convert to BGR for cv2.imwrite
                face_image_bgr = cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR)
            else:
                face_image_bgr = face_image
            
            # Save to temporary file for DeepFace
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                cv2.imwrite(tmp_path, face_image_bgr)
            
            try:
                # Use opencv detector (lightweight) with anti-spoofing
                # For cropped faces, opencv should detect the face easily
                face_objs = DeepFace.extract_faces(
                    img_path=tmp_path,
                    detector_backend="opencv",  # Lightweight detector
                    enforce_detection=False,  # Don't fail if face not detected
                    anti_spoofing=True,  # Enable anti-spoofing
                    align=False,  # Already aligned
                )
                
                if not face_objs or len(face_objs) == 0:
                    return AntiSpoofResult(
                        is_live=False,
                        live_score=0.0,
                        fake_score=1.0,
                        threshold=0.5,
                        details={"reason": "no_face_detected"},
                    )
                
                # Get the first face result
                face_obj = face_objs[0]
                is_real = face_obj.get("is_real", False)
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            # DeepFace returns boolean, we convert to scores
            # If is_real is True, live_score = 1.0, fake_score = 0.0
            # If is_real is False, live_score = 0.0, fake_score = 1.0
            live_score = 1.0 if is_real else 0.0
            fake_score = 1.0 - live_score
            
            print(
                f"[ANTISPOOF] DeepFace result: is_real={is_real}, "
                f"live_score={live_score:.3f}, fake_score={fake_score:.3f}"
            )
            
            return AntiSpoofResult(
                is_live=is_real,
                live_score=live_score,
                fake_score=fake_score,
                threshold=0.5,  # DeepFace uses 0.5 threshold internally
                details={
                    "backend": "deepface",
                    "is_real": is_real,
                },
            )
            
        except Exception as e:
            print(f"[ANTISPOOF] Error during DeepFace anti-spoofing: {e}")
            # On error, fail closed (reject as spoof) for security
            return AntiSpoofResult(
                is_live=False,
                live_score=0.0,
                fake_score=1.0,
                threshold=0.5,
                details={"error": str(e), "reason": "exception"},
            )


_antispoof_service: AntiSpoofingService | None = None


def get_antispoof_service() -> AntiSpoofingService:
    """
    Get or create the anti-spoofing service instance (singleton).
    """
    global _antispoof_service
    if _antispoof_service is None:
        _antispoof_service = AntiSpoofingService()
    return _antispoof_service

