from typing import Literal
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