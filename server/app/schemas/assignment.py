from datetime import date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class AssignmentBase(BaseModel):
    person_id: str
    site_id: UUID
    shift_id: UUID
    title: Optional[str] = None
    rate: float = 0
    effective_from: date
    effective_to: Optional[date] = None

class AssignmentCreate(AssignmentBase):
    pass

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    rate: Optional[float] = None
    effective_to: Optional[date] = None

class AssignmentRead(AssignmentBase):
    id: UUID
    
    class Config:
        from_attributes = True
