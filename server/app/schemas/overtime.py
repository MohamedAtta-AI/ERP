"""
Overtime Request Pydantic Schemas for API validation.
"""

from typing import Optional
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class OvertimeRequestCreate(BaseModel):
    """Schema for creating an overtime request."""
    person_id: str = Field(..., min_length=6, max_length=6)
    attendance_id: Optional[UUID] = None
    overtime_date: date  # Renamed from 'date' to avoid conflict
    hours: float = Field(..., ge=0)
    notes: Optional[str] = None


class OvertimeRequestRead(BaseModel):
    """Schema for reading overtime request data."""
    id: UUID
    person_id: str
    person_name: str
    attendance_id: Optional[UUID] = None
    overtime_date: date  # Renamed from 'date' to avoid conflict
    hours: float
    status: str
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_by_person_id: Optional[str] = None
    approved_by_person_id: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OvertimeRequestUpdate(BaseModel):
    """Schema for updating an overtime request (approval/rejection)."""
    status: str = Field(..., pattern="^(approved|rejected)$")
    rejection_reason: Optional[str] = Field(None, max_length=500)

