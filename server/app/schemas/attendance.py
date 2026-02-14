from typing import Literal, Optional
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field


class AttendanceRequest(BaseModel):
    person_id: str = Field(..., min_length=6, max_length=6)
    site_id: UUID
    shift_id: UUID
    type: Literal["check-in", "check-out"]


class AttendanceResponse(BaseModel):
    attendance_id: UUID
    person_id: str
    full_name: str
    timestamp: datetime
    similarity: float


class AttendanceRead(BaseModel):
    id: UUID
    person_id: str
    person_name: str
    attendance_date: date
    check_in: datetime
    check_out: Optional[datetime] = None
    status: str
    location_name: Optional[str] = None
    shift_name: Optional[str] = None
    assignment_title: Optional[str] = None
    assignment_rate: Optional[float] = None

    class Config:
        from_attributes = True
