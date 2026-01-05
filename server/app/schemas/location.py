"""
Location Pydantic Schemas for API validation.
"""

from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    """Schema for creating a location."""
    name: str = Field(..., min_length=1, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)


class LocationRead(BaseModel):
    """Schema for reading location data."""
    id: UUID
    name: str
    city: Optional[str] = None
    address: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

