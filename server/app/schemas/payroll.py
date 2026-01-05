"""
Payroll Pydantic Schemas for API validation.
"""

from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class PayrollPeriodCreate(BaseModel):
    """Schema for creating a payroll period."""
    start_date: date
    end_date: date


class PayrollPeriodRead(BaseModel):
    """Schema for reading payroll period data."""
    id: UUID
    start_date: date
    end_date: date
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PayrollPeriodUpdate(BaseModel):
    """Schema for updating a payroll period."""
    status: Optional[str] = None


class PayrollRunCreate(BaseModel):
    """Schema for creating a payroll run."""
    payroll_period_id: UUID
    location_id: Optional[UUID] = None
    notes: Optional[str] = None


class PayrollRunRead(BaseModel):
    """Schema for reading payroll run data."""
    id: UUID
    payroll_period_id: UUID
    location_id: Optional[UUID] = None
    location_name: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_by_person_id: Optional[str] = None
    approved_by_person_id: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PayrollRunUpdate(BaseModel):
    """Schema for updating a payroll run."""
    status: Optional[str] = None
    notes: Optional[str] = None


class PayrollRunLineRead(BaseModel):
    """Schema for reading payroll run line item."""
    id: UUID
    component_id: Optional[UUID] = None
    component_name_snapshot: Optional[str] = None
    kind: str
    amount: float
    
    class Config:
        from_attributes = True


class PayrollRunEmployeeRead(BaseModel):
    """Schema for reading payroll run employee data."""
    id: UUID
    person_id: str
    person_name: str
    base_salary_amount: Optional[float] = None
    gross: float
    deductions: float
    net: float
    total_hours: float
    total_days: int
    lines: List[PayrollRunLineRead] = []
    
    class Config:
        from_attributes = True


class PayrollRunDetailRead(BaseModel):
    """Schema for reading detailed payroll run data."""
    id: UUID
    payroll_period_id: UUID
    location_id: Optional[UUID] = None
    location_name: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    employees: List[PayrollRunEmployeeRead] = []
    
    class Config:
        from_attributes = True


class SalaryComponentCreate(BaseModel):
    """Schema for creating a salary component."""
    name: str = Field(..., min_length=1, max_length=100)
    kind: str = Field(..., pattern="^(earning|deduction)$")
    type: str = Field(..., pattern="^(base_salary|overtime|allowance|incentive|tax|other)$")
    amount_type: str = Field(..., pattern="^(fixed|per_day|per_hour|percentage)$")
    amount: float = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=500)


class SalaryComponentRead(BaseModel):
    """Schema for reading salary component data."""
    id: UUID
    name: str
    kind: str
    type: str
    amount_type: str
    amount: float
    active: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SalaryComponentUpdate(BaseModel):
    """Schema for updating a salary component."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[float] = Field(None, ge=0)
    active: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=500)

