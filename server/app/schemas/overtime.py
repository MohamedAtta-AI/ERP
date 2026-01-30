from typing import Optional, Literal
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field


class OvertimeRequestCreate(BaseModel):
    person_id: str = Field(..., min_length=6, max_length=6)
    attendance_id: Optional[UUID] = None
    overtime_date: date
    hours: float = Field(..., ge=0)
    notes: Optional[str] = None


class OvertimeRequestUpdate(BaseModel):
    status: Literal["approved", "rejected"]
    rejection_reason: Optional[str] = None


class OvertimeRequestRead(BaseModel):
    id: UUID
    person_id: str
    person_name: str
    attendance_id: Optional[UUID] = None
    overtime_date: date
    hours: float
    status: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
