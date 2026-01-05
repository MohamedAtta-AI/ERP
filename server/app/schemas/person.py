"""
Person/Employee Pydantic Schemas for API validation.
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field


class PersonCreate(BaseModel):
    """Schema for creating a new person."""
    full_name: str = Field(..., min_length=2, max_length=255)
    identity_number: Optional[str] = Field(None, max_length=50)
    dob: Optional[date] = None
    sex: Optional[str] = Field(None, pattern="^[MF]$")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    # Extended fields (admin only for monetary fields)
    hire_date: Optional[date] = None
    employment_status: Optional[str] = None
    worker_type: Optional[str] = None
    grade: Optional[str] = Field(None, max_length=50)
    contract_type: Optional[str] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    pay_cycle: Optional[str] = None
    payroll_group_id: Optional[str] = None
    probation_status: Optional[bool] = None
    overtime_eligible: Optional[bool] = None
    insurance_enrollment_status: Optional[str] = None
    insurance_number: Optional[str] = Field(None, max_length=50)
    tax_id: Optional[str] = Field(None, max_length=50)
    tax_residency_status: Optional[str] = Field(None, max_length=50)
    payment_method: Optional[str] = None
    bank_name: Optional[str] = Field(None, max_length=100)
    iban: Optional[str] = Field(None, max_length=34)
    account_number: Optional[str] = Field(None, max_length=50)
    account_holder_name: Optional[str] = Field(None, max_length=255)
    branch_code: Optional[str] = Field(None, max_length=20)
    wallet_provider: Optional[str] = Field(None, max_length=50)
    wallet_number: Optional[str] = Field(None, max_length=50)
    payroll_currency: Optional[str] = Field(None, max_length=3)
    payment_status: Optional[str] = None
    role_id: Optional[str] = None
    supervisor_id: Optional[str] = None
    password: Optional[str] = None  # For setting initial password


class PersonRead(BaseModel):
    """Schema for reading person data."""
    id: str = Field(..., alias="person_id")
    full_name: str
    identity_number: Optional[str] = None
    dob: Optional[date] = None
    sex: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    status: str
    role: Optional[str] = None  # Role name
    has_face_enrolled: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class PersonUpdate(BaseModel):
    """Schema for updating a person."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    identity_number: Optional[str] = Field(None, max_length=50)
    dob: Optional[date] = None
    sex: Optional[str] = Field(None, pattern="^[MF]$")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None
    # Extended fields (admin only for monetary fields)
    hire_date: Optional[date] = None
    employment_status: Optional[str] = None
    worker_type: Optional[str] = None
    grade: Optional[str] = Field(None, max_length=50)
    contract_type: Optional[str] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    pay_cycle: Optional[str] = None
    payroll_group_id: Optional[str] = None
    probation_status: Optional[bool] = None
    overtime_eligible: Optional[bool] = None
    insurance_enrollment_status: Optional[str] = None
    insurance_number: Optional[str] = Field(None, max_length=50)
    tax_id: Optional[str] = Field(None, max_length=50)
    tax_residency_status: Optional[str] = Field(None, max_length=50)
    payment_method: Optional[str] = None
    bank_name: Optional[str] = Field(None, max_length=100)
    iban: Optional[str] = Field(None, max_length=34)
    account_number: Optional[str] = Field(None, max_length=50)
    account_holder_name: Optional[str] = Field(None, max_length=255)
    branch_code: Optional[str] = Field(None, max_length=20)
    wallet_provider: Optional[str] = Field(None, max_length=50)
    wallet_number: Optional[str] = Field(None, max_length=50)
    payroll_currency: Optional[str] = Field(None, max_length=3)
    payment_status: Optional[str] = None
    role_id: Optional[str] = None
    supervisor_id: Optional[str] = None
    password: Optional[str] = None  # For password updates


class FaceEnrollRequest(BaseModel):
    """Schema for face enrollment (metadata, image is file upload)."""
    pass  # Image is handled via multipart form


class FaceEnrollResponse(BaseModel):
    """Response after successful face enrollment."""
    person_id: str
    message: str = "Face enrolled successfully"
    embedding_size: int = 128


