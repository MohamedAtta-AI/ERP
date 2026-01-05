"""
Skill Pydantic Schemas for API validation.
"""

from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    """Schema for creating a skill."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class SkillRead(BaseModel):
    """Schema for reading skill data."""
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class PersonSkillCreate(BaseModel):
    """Schema for assigning a skill to a person."""
    person_id: str = Field(..., min_length=6, max_length=6)
    skill_id: UUID
    certified_at: Optional[date] = None
    expires_at: Optional[date] = None


class PersonSkillRead(BaseModel):
    """Schema for reading person-skill relationship."""
    person_id: str
    skill_id: UUID
    skill_name: str
    certified_at: Optional[date] = None
    expires_at: Optional[date] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SkillLocationPriceCreate(BaseModel):
    """Schema for creating skill-location pricing."""
    skill_id: UUID
    location_id: UUID
    price: float = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


class SkillLocationPriceRead(BaseModel):
    """Schema for reading skill-location pricing."""
    skill_id: UUID
    location_id: UUID
    skill_name: str
    location_name: str
    price: float
    currency: str
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

