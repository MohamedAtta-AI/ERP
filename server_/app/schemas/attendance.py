"""Attendance schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AttendanceCheckIn(BaseModel):
    """Check-in request."""
    employee_id: str
    location: Optional[str] = None


class AttendanceCheckOut(BaseModel):
    """Check-out request."""
    employee_id: str


class AttendanceResponse(BaseModel):
    """Attendance record response."""
    id: int
    employee_id: int
    check_in_time: datetime
    check_out_time: Optional[datetime]
    location: Optional[str]
    device_info: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceHistoryResponse(BaseModel):
    """Attendance history response."""
    id: int
    employee_id: int
    employee_name: str
    employee_code: str
    check_in_time: datetime
    check_out_time: Optional[datetime]
    location: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
