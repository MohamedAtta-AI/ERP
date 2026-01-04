"""Attendance model using SQLModel."""
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, DateTime, Text, func
from datetime import datetime
from typing import Optional


class AttendanceBase(SQLModel):
    """Base attendance model."""
    check_in_time: datetime = Field(sa_column=Column(DateTime(timezone=True), index=True))
    check_out_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    location: Optional[str] = Field(default=None, max_length=255, sa_column=Column(String(255)))
    device_info: Optional[str] = Field(default=None, sa_column=Column(Text))


class Attendance(AttendanceBase, table=True):
    """Attendance database model."""
    __tablename__ = "attendance"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id", ondelete="CASCADE", index=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    
    # Relationships
    employee: "Employee" = Relationship(back_populates="attendance_records")
