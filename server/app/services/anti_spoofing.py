"""Simple anti-spoofing checks for face recognition."""
import cv2
import numpy as np
from typing import Dict


def check_liveness(image: np.ndarray, face_box: tuple) -> Dict[str, any]:
    """
    Perform basic passive liveness checks.
    
    Args:
        image: Full image
        face_box: (x, y, w, h) face bounding box
        
    Returns:
        Dict with liveness score and details
    """
    x, y, w, h = face_box
    
    # Extract face region
    face_region = image[y:y+h, x:x+w]
    
    if face_region.size == 0:
        return {
            "is_live": False,
            "score": 0.0,
            "reason": "Invalid face region"
        }
    
    # Check 1: Face size consistency (spoofed images often have very uniform sizes)
    face_area = w * h
    image_area = image.shape[0] * image.shape[1]
    face_ratio = face_area / image_area
    
    # Real faces typically occupy 5-40% of image
    size_check = 0.05 <= face_ratio <= 0.40
    
    # Check 2: Image quality (printed photos often have lower quality)
    gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY) if len(face_region.shape) == 3 else face_region
    
    # Calculate Laplacian variance (sharpness)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Real faces typically have higher sharpness (>50)
    sharpness_check = laplacian_var > 50
    
    # Check 3: Color distribution (printed photos may have different color characteristics)
    if len(face_region.shape) == 3:
        # Calculate color variance
        color_variance = np.var(face_region.reshape(-1, 3), axis=0).mean()
        color_check = color_variance > 500  # Real faces have more color variation
    else:
        color_check = True
    
    # Check 4: Brightness distribution (real faces have natural lighting variation)
    brightness_std = np.std(gray)
    brightness_check = brightness_std > 15  # Real faces have natural variation
    
    # Calculate overall liveness score
    checks_passed = sum([size_check, sharpness_check, color_check, brightness_check])
    liveness_score = checks_passed / 4.0
    
    is_live = liveness_score >= 0.75  # Require at least 3/4 checks to pass
    
    reasons = []
    if not size_check:
        reasons.append("Face size unusual")
    if not sharpness_check:
        reasons.append("Image too blurry")
    if not color_check:
        reasons.append("Color distribution suspicious")
    if not brightness_check:
        reasons.append("Lighting too uniform")
    
    return {
        "is_live": is_live,
        "score": liveness_score,
        "checks": {
            "size": size_check,
            "sharpness": sharpness_check,
            "color": color_check,
            "brightness": brightness_check
        },
        "reason": "; ".join(reasons) if reasons else "Passed all checks"
    }

