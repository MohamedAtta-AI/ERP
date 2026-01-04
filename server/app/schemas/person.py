"""
Person/Employee Pydantic Schemas for API validation.
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field


class PersonCreate(BaseModel):
    """Schema for creating a new person."""
    full_name: str = Field(..., min_length=2, max_length=255)
    identity_number: Optional[str] = Field(None, max_length=50)
    dob: Optional[date] = None
    sex: Optional[str] = Field(None, pattern="^[MF]$")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)


class PersonRead(BaseModel):
    """Schema for reading person data."""
    id: str = Field(..., alias="person_id")
    full_name: str
    identity_number: Optional[str] = None
    dob: Optional[date] = None
    sex: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    status: str
    has_face_enrolled: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class PersonUpdate(BaseModel):
    """Schema for updating a person."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    identity_number: Optional[str] = Field(None, max_length=50)
    dob: Optional[date] = None
    sex: Optional[str] = Field(None, pattern="^[MF]$")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None


class FaceEnrollRequest(BaseModel):
    """Schema for face enrollment (metadata, image is file upload)."""
    pass  # Image is handled via multipart form


class FaceEnrollResponse(BaseModel):
    """Response after successful face enrollment."""
    person_id: str
    message: str = "Face enrolled successfully"
    embedding_size: int = 128

