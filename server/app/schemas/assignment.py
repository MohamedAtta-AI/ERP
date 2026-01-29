from typing import Optional
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    person_id: str = Field(..., min_length=6, max_length=6)
    location_id: UUID
    shift_id: UUID
    title: Optional[str] = Field(None, max_length=100)
    rate: Optional[float] = Field(None, ge=0)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


class AssignmentRead(BaseModel):
    id: UUID
    person_id: str
    person_name: str
    location_id: UUID
    location_name: str
    shift_id: UUID
    shift_name: Optional[str] = None
    title: Optional[str] = None
    rate: Optional[float] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    rate: Optional[float] = Field(None, ge=0)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None