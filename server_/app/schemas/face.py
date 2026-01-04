"""Face-related schemas."""
from pydantic import BaseModel
from typing import Optional


class FaceEnrollRequest(BaseModel):
    """Face enrollment request (file upload)."""
    pass  # File will be handled separately


class FaceVerifyResponse(BaseModel):
    """Face verification response."""
    employee_id: str
    full_name: str
    email: Optional[str]
    department: Optional[str]
    similarity_score: float
    match_found: bool
