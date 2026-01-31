from datetime import date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from server.db.enums import Role, PersonStatus, PayCycle, WorkerType, PaymentMethod

class PaymentInfoBase(BaseModel):
    payment_method: PaymentMethod
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    branch_code: Optional[str] = None
    wallet_provider: Optional[str] = None
    wallet_number: Optional[str] = None

class PaymentInfoCreate(PaymentInfoBase):
    person_id: str

class PaymentInfoRead(PaymentInfoBase):
    person_id: str

class PersonBase(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: str
    nationalID: Optional[str] = None
    passport: Optional[str] = None
    dob: Optional[date] = None
    sex: Optional[str] = None
    street_address: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    role: Role
    status: PersonStatus = PersonStatus.ACTIVE
    worker_type: Optional[WorkerType] = None
    pay_cycle: Optional[PayCycle] = None
    supervisor_id: Optional[str] = None
    overtime_eligible: bool = True
    incentive_eligible: bool = True
    hire_date: Optional[date] = None

class PersonCreate(PersonBase):
    password_hash: Optional[str] = None # Optional, backend can generate default

class PersonUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    role: Optional[Role] = None
    status: Optional[PersonStatus] = None
    supervisor_id: Optional[str] = None

class PersonRead(PersonBase):
    id: str
    
    class Config:
        from_attributes = True
