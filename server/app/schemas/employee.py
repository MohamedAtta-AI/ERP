"""Employee schemas."""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class EmployeeCreate(BaseModel):
    """Employee registration request."""
    full_name: str
    email: EmailStr
    department: str
    phone: Optional[str] = None
    position: Optional[str] = None


class EmployeeResponse(BaseModel):
    """Employee response."""
    id: int
    employee_id: str
    full_name: str
    email: Optional[str]
    department: Optional[str]
    phone: Optional[str]
    position: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
