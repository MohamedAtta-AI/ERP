"""Employee schemas."""

from pydantic import BaseModel
from typing import List


class FaceEnrollmentRequest(BaseModel):
    """Request to enroll multiple face images."""

    images: List[str]  # List of base64-encoded image strings


class FaceEnrollmentResponse(BaseModel):
    """Response after enrolling faces."""

    message: str
    employee_id: str
    enrolled_count: int
    embedding_count: int
