"""
Shift Pydantic Schemas for API validation.
"""

from typing import Optional
from datetime import datetime, time
from uuid import UUID
from pydantic import BaseModel, Field


class ShiftCreate(BaseModel):
    """Schema for creating a shift."""
    name: Optional[str] = Field(None, max_length=100)
    starts_at: time
    ends_at: time
    is_overnight: bool = False


class ShiftRead(BaseModel):
    """Schema for reading shift data."""
    id: UUID
    name: Optional[str] = None
    starts_at: time
    ends_at: time
    is_overnight: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ShiftUpdate(BaseModel):
    """Schema for updating a shift."""
    name: Optional[str] = Field(None, max_length=100)
    starts_at: Optional[time] = None
    ends_at: Optional[time] = None
    is_overnight: Optional[bool] = None
    is_active: Optional[bool] = None

