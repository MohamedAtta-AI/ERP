"""
Attendance Pydantic Schemas for API validation.
"""

from typing import Optional
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field


class AttendanceVerifyRequest(BaseModel):
    """
    Schema for face verification request.
    Note: The actual image is sent as multipart form data, not in this schema.
    """
    location_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None


class AttendanceVerifyResponse(BaseModel):
    """Response from face verification endpoint."""
    match_found: bool
    person_id: Optional[str] = Field(None, alias="employee_id")
    full_name: Optional[str] = None
    department: Optional[str] = None
    similarity_score: Optional[float] = None
    is_real: Optional[bool] = None  # Anti-spoofing result
    message: Optional[str] = None
    
    class Config:
        populate_by_name = True


class AttendanceCheckInRequest(BaseModel):
    """Request to record a check-in after successful verification."""
    person_id: str = Field(..., alias="employee_id", min_length=6, max_length=6)
    location_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None
    
    class Config:
        populate_by_name = True


class AttendanceCheckInResponse(BaseModel):
    """Response after successful check-in."""
    attendance_id: UUID
    person_id: str
    full_name: str
    check_in_time: datetime
    location: Optional[str] = None
    message: str = "Check-in recorded successfully"


class AttendanceCheckOutRequest(BaseModel):
    """Request to record a check-out."""
    person_id: str = Field(..., alias="employee_id", min_length=6, max_length=6)
    
    class Config:
        populate_by_name = True


class AttendanceCheckOutResponse(BaseModel):
    """Response after successful check-out."""
    attendance_id: UUID
    person_id: str
    check_out_time: datetime
    total_hours: Optional[float] = None
    message: str = "Check-out recorded successfully"


class AttendanceRead(BaseModel):
    """Schema for reading attendance records."""
    id: UUID
    person_id: str
    person_name: str
    attendance_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: str
    location_name: Optional[str] = None
    shift_name: Optional[str] = None
    similarity_score: Optional[float] = None
    is_real: Optional[bool] = None
    
    class Config:
        from_attributes = True


