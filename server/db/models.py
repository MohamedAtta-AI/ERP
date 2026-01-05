"""
OnTime ERP Database Models

Uses SQLModel (Pydantic + SQLAlchemy) for type-safe database models.
Follows the MVP schema design with pgvector for face embeddings.
"""

from typing import Optional, List
from datetime import datetime, date, time
from uuid import UUID, uuid4
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, Text, Index
from pgvector.sqlalchemy import Vector


# =============================================================================
# Enums
# =============================================================================

class PersonStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"


class EmploymentStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"


class WorkerType(str, Enum):
    PERMANENT = "permanent"
    TEMP = "temp"
    DAILY = "daily"
    CONTRACTOR = "contractor"


class ContractType(str, Enum):
    FIXED_TERM = "fixed_term"
    INDEFINITE = "indefinite"
    DAILY_WAGE = "daily_wage"
    PROJECT_BASED = "project_based"


class PayCycle(str, Enum):
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    DAILY = "daily"


class InsuranceStatus(str, Enum):
    ENROLLED = "enrolled"
    EXEMPT = "exempt"
    PENDING = "pending"


class PaymentMethod(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    WALLET = "wallet"


class PaymentStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    HOLD = "hold"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    OVERTIME_PENDING = "overtime_pending"
    OVERTIME_APPROVED = "overtime_approved"


class Sex(str, Enum):
    MALE = "M"
    FEMALE = "F"


# =============================================================================
# Role Model
# =============================================================================

class Role(SQLModel, table=True):
    """User roles for RBAC (admin, supervisor, worker)"""
    __tablename__ = "role"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    persons: List["Person"] = Relationship(back_populates="role")


# =============================================================================
# Location Model
# =============================================================================

class Location(SQLModel, table=True):
    """Work locations/sites (Location = Client/Site, no separate Client model)"""
    __tablename__ = "location"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    city: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
    contract_document_url: Optional[str] = Field(default=None, max_length=500)
    contract_name: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    attendances: List["Attendance"] = Relationship(back_populates="location")


# =============================================================================
# Shift Model
# =============================================================================

class Shift(SQLModel, table=True):
    """Work shifts with start/end times"""
    __tablename__ = "shift"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: Optional[str] = Field(default=None, max_length=100)
    starts_at: time
    ends_at: time
    is_overnight: bool = Field(default=False)  # For shifts that cross midnight
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    attendances: List["Attendance"] = Relationship(back_populates="shift")


# =============================================================================
# Person Model (Employee/Worker)
# =============================================================================

class Person(SQLModel, table=True):
    """
    Person model representing employees/workers.
    Uses 6-character alphanumeric ID as primary key.
    Stores face embedding as pgvector for similarity search.
    """
    __tablename__ = "person"
    
    # 6-character alphanumeric ID (e.g., "A1B2C3")
    id: str = Field(
        sa_column=Column(String(6), primary_key=True),
        max_length=6,
        min_length=6,
    )
    
    # Personal info
    full_name: str = Field(max_length=255, index=True)
    identity_number: Optional[str] = Field(default=None, max_length=50, unique=True)
    dob: Optional[date] = Field(default=None)
    sex: Optional[Sex] = Field(default=None)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255, unique=True)
    
    # Employment info
    status: PersonStatus = Field(default=PersonStatus.ACTIVE)
    department: Optional[str] = Field(default=None, max_length=100)
    position: Optional[str] = Field(default=None, max_length=100)
    
    # Extended employment fields
    hire_date: Optional[date] = Field(default=None)
    employment_status: Optional[EmploymentStatus] = Field(default=None)
    worker_type: Optional[WorkerType] = Field(default=None)
    grade: Optional[str] = Field(default=None, max_length=50)
    contract_type: Optional[ContractType] = Field(default=None)
    contract_start_date: Optional[date] = Field(default=None)
    contract_end_date: Optional[date] = Field(default=None)
    pay_cycle: Optional[PayCycle] = Field(default=None)
    payroll_group_id: Optional[UUID] = Field(default=None, foreign_key="payroll_group.id")
    probation_status: bool = Field(default=False)
    overtime_eligible: bool = Field(default=True)
    
    # Insurance and tax fields
    insurance_enrollment_status: Optional[InsuranceStatus] = Field(default=None)
    insurance_number: Optional[str] = Field(default=None, max_length=50)
    tax_id: Optional[str] = Field(default=None, max_length=50)
    tax_residency_status: Optional[str] = Field(default=None, max_length=50)
    
    # Payment fields
    payment_method: Optional[PaymentMethod] = Field(default=None)
    bank_name: Optional[str] = Field(default=None, max_length=100)
    iban: Optional[str] = Field(default=None, max_length=34)
    account_number: Optional[str] = Field(default=None, max_length=50)
    account_holder_name: Optional[str] = Field(default=None, max_length=255)
    branch_code: Optional[str] = Field(default=None, max_length=20)
    wallet_provider: Optional[str] = Field(default=None, max_length=50)
    wallet_number: Optional[str] = Field(default=None, max_length=50)
    payroll_currency: str = Field(default="EGP", max_length=3)
    payment_status: Optional[PaymentStatus] = Field(default=None)
    
    # Authentication
    password_hash: Optional[str] = Field(default=None, max_length=255)
    
    # Foreign keys
    role_id: Optional[UUID] = Field(default=None, foreign_key="role.id")
    supervisor_id: Optional[str] = Field(default=None, foreign_key="person.id")
    
    # Face recognition - 128-dimensional embedding vector
    face_embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(128))
    )
    face_image_url: Optional[str] = Field(default=None, max_length=500)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    role: Optional[Role] = Relationship(back_populates="persons")
    supervisor: Optional["Person"] = Relationship(
        sa_relationship_kwargs={"remote_side": "Person.id"}
    )
    attendances: List["Attendance"] = Relationship(
        back_populates="person",
        sa_relationship_kwargs={"foreign_keys": "[Attendance.person_id]"}
    )
    attendances_taken: List["Attendance"] = Relationship(
        back_populates="taken_by",
        sa_relationship_kwargs={"foreign_keys": "[Attendance.taken_by_person_id]"}
    )


# =============================================================================
# Attendance Model
# =============================================================================

class Attendance(SQLModel, table=True):
    """
    Attendance records for daily check-in/check-out.
    Stores verification image URL for audit trail.
    """
    __tablename__ = "attendance"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    person_id: str = Field(foreign_key="person.id", index=True)
    taken_by_person_id: Optional[str] = Field(default=None, foreign_key="person.id")
    location_id: Optional[UUID] = Field(default=None, foreign_key="location.id")
    shift_id: Optional[UUID] = Field(default=None, foreign_key="shift.id")
    
    # Attendance data
    attendance_date: date = Field(index=True)
    check_in: Optional[datetime] = Field(default=None)
    check_out: Optional[datetime] = Field(default=None)
    
    # Verification data
    image_url: Optional[str] = Field(default=None, max_length=500)
    similarity_score: Optional[float] = Field(default=None)
    is_real: Optional[bool] = Field(default=None)  # Anti-spoofing result
    
    # Status
    status: AttendanceStatus = Field(default=AttendanceStatus.PRESENT)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    person: Person = Relationship(
        back_populates="attendances",
        sa_relationship_kwargs={"foreign_keys": "[Attendance.person_id]"}
    )
    taken_by: Optional[Person] = Relationship(
        back_populates="attendances_taken",
        sa_relationship_kwargs={"foreign_keys": "[Attendance.taken_by_person_id]"}
    )
    location: Optional[Location] = Relationship(back_populates="attendances")
    shift: Optional[Shift] = Relationship(back_populates="attendances")
    
    class Config:
        # Create composite index on person_id + attendance_date
        pass


# =============================================================================
# Document Model
# =============================================================================

class Document(SQLModel, table=True):
    """Documents associated with persons (ID cards, contracts, etc.)"""
    __tablename__ = "document"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    person_id: str = Field(foreign_key="person.id", index=True)
    uploaded_by_person_id: Optional[str] = Field(default=None, foreign_key="person.id")
    
    # Document info
    type: str = Field(max_length=50, index=True)  # e.g., "id_card", "contract", "certificate"
    storage_url: str = Field(max_length=500)
    file_name: Optional[str] = Field(default=None, max_length=255)
    file_size: Optional[int] = Field(default=None)  # Size in bytes
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships - specify foreign_keys to disambiguate
    person: Person = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Document.person_id"}
    )
    uploaded_by: Optional[Person] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Document.uploaded_by_person_id"}
    )


# =============================================================================
# Skill Models
# =============================================================================

class Skill(SQLModel, table=True):
    """Skills that workers can have"""
    __tablename__ = "skill"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    person_skills: List["PersonSkill"] = Relationship(back_populates="skill")
    location_prices: List["SkillLocationPrice"] = Relationship(back_populates="skill")


class PersonSkill(SQLModel, table=True):
    """Many-to-many relationship between Person and Skill"""
    __tablename__ = "person_skill"
    
    person_id: str = Field(foreign_key="person.id", primary_key=True)
    skill_id: UUID = Field(foreign_key="skill.id", primary_key=True)
    
    # Optional: certification date, expiry, etc.
    certified_at: Optional[date] = Field(default=None)
    expires_at: Optional[date] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    person: Person = Relationship()
    skill: Skill = Relationship(back_populates="person_skills")


class SkillLocationPrice(SQLModel, table=True):
    """Pricing for skills at specific locations"""
    __tablename__ = "skill_location_price"
    
    skill_id: UUID = Field(foreign_key="skill.id", primary_key=True)
    location_id: UUID = Field(foreign_key="location.id", primary_key=True)
    
    price: float = Field(ge=0)  # Price per hour or per day
    currency: str = Field(default="USD", max_length=3)
    effective_from: Optional[date] = Field(default=None)
    effective_to: Optional[date] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    skill: Skill = Relationship(back_populates="location_prices")
    location: Location = Relationship()


# =============================================================================
# Assignment Model
# =============================================================================

class Assignment(SQLModel, table=True):
    """Assignments of persons to locations and shifts"""
    __tablename__ = "assignment"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    person_id: str = Field(foreign_key="person.id", index=True)
    location_id: UUID = Field(foreign_key="location.id", index=True)
    shift_id: UUID = Field(foreign_key="shift.id", index=True)
    
    # Assignment details
    title: Optional[str] = Field(default=None, max_length=100)
    rate: Optional[float] = Field(default=None, ge=0)  # Hourly/daily rate
    
    # Effective dates
    effective_from: Optional[date] = Field(default=None, index=True)
    effective_to: Optional[date] = Field(default=None)
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    person: Person = Relationship()
    location: Location = Relationship()
    shift: Shift = Relationship()


# =============================================================================
# Overtime Request Model
# =============================================================================

class OvertimeRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OvertimeRequest(SQLModel, table=True):
    """Overtime requests for attendance reconciliation"""
    __tablename__ = "overtime_request"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    person_id: str = Field(foreign_key="person.id", index=True)
    attendance_id: Optional[UUID] = Field(default=None, foreign_key="attendance.id")
    created_by_person_id: Optional[str] = Field(default=None, foreign_key="person.id")
    approved_by_person_id: Optional[str] = Field(default=None, foreign_key="person.id")
    
    # Overtime data
    overtime_date: date = Field(index=True)  # Renamed from 'date' to avoid conflict with type
    hours: float = Field(ge=0)
    status: OvertimeRequestStatus = Field(default=OvertimeRequestStatus.PENDING)
    
    # Notes
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    rejection_reason: Optional[str] = Field(default=None, max_length=500)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = Field(default=None)
    
    # Relationships - specify foreign_keys to disambiguate
    person: Person = Relationship(
        sa_relationship_kwargs={"foreign_keys": "OvertimeRequest.person_id"}
    )
    created_by: Optional[Person] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "OvertimeRequest.created_by_person_id"}
    )
    approved_by: Optional[Person] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "OvertimeRequest.approved_by_person_id"}
    )
    attendance: Optional[Attendance] = Relationship()


# =============================================================================
# Salary Component Models
# =============================================================================

class ComponentKind(str, Enum):
    EARNING = "earning"
    DEDUCTION = "deduction"


class ComponentType(str, Enum):
    BASE_SALARY = "base_salary"
    OVERTIME = "overtime"
    ALLOWANCE = "allowance"
    INCENTIVE = "incentive"
    TAX = "tax"
    INSURANCE = "insurance"
    LOAN_INSTALLMENT = "loan_installment"
    ADVANCE_REPAYMENT = "advance_repayment"
    PENALTY = "penalty"
    OTHER = "other"


class AmountType(str, Enum):
    FIXED = "fixed"
    PER_DAY = "per_day"
    PER_HOUR = "per_hour"
    PERCENTAGE = "percentage"


class SalaryComponent(SQLModel, table=True):
    """Salary components (earnings and deductions)"""
    __tablename__ = "salary_component"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    name: str = Field(max_length=100, index=True)
    kind: ComponentKind
    type: ComponentType
    amount_type: AmountType
    amount: float = Field(ge=0)  # Base amount (can be overridden per employee)
    active: bool = Field(default=True)
    
    # Metadata fields
    taxable: bool = Field(default=True)  # Whether component is included in tax calculations
    insurable: bool = Field(default=True)  # Whether component is included in insurance calculations
    max_amount: Optional[float] = Field(default=None)  # Maximum cap for this component
    max_percentage: Optional[float] = Field(default=None)  # Maximum percentage of base salary
    priority: int = Field(default=0)  # Deduction order (lower number = deducted first)
    cost_allocation_rule: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON for client billing allocation
    
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    employee_components: List["EmployeeComponent"] = Relationship(back_populates="component")
    payroll_lines: List["PayrollRunLine"] = Relationship(back_populates="component")


class EmployeeComponent(SQLModel, table=True):
    """Employee-specific overrides for salary components"""
    __tablename__ = "employee_component"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    person_id: str = Field(foreign_key="person.id", index=True)
    component_id: UUID = Field(foreign_key="salary_component.id", index=True)
    
    # Override value (if None, use component's default amount)
    value_override: Optional[float] = Field(default=None, ge=0)
    
    # Effective dates
    effective_from: Optional[date] = Field(default=None)
    effective_to: Optional[date] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    person: Person = Relationship()
    component: SalaryComponent = Relationship(back_populates="employee_components")


# =============================================================================
# Payroll Models
# =============================================================================

class PayrollPeriodStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    LOCKED = "locked"


class PayrollRunStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    LOCKED = "locked"


class PayrollPeriod(SQLModel, table=True):
    """Payroll periods (typically monthly)"""
    __tablename__ = "payroll_period"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    start_date: date = Field(index=True)
    end_date: date = Field(index=True)
    status: PayrollPeriodStatus = Field(default=PayrollPeriodStatus.OPEN)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    payroll_runs: List["PayrollRun"] = Relationship(back_populates="period")


class PayrollRun(SQLModel, table=True):
    """Payroll run for a specific period and location"""
    __tablename__ = "payroll_run"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    payroll_period_id: UUID = Field(foreign_key="payroll_period.id", index=True)
    location_id: Optional[UUID] = Field(default=None, foreign_key="location.id", index=True)
    created_by_person_id: Optional[str] = Field(default=None, foreign_key="person.id")
    approved_by_person_id: Optional[str] = Field(default=None, foreign_key="person.id")
    
    status: PayrollRunStatus = Field(default=PayrollRunStatus.DRAFT)
    
    # Notes
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    period: PayrollPeriod = Relationship(back_populates="payroll_runs")
    location: Optional[Location] = Relationship()
    created_by: Optional[Person] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "PayrollRun.created_by_person_id"}
    )
    approved_by: Optional[Person] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "PayrollRun.approved_by_person_id"}
    )
    employees: List["PayrollRunEmployee"] = Relationship(back_populates="payroll_run")


class PayrollRunEmployee(SQLModel, table=True):
    """Employee payroll summary for a payroll run"""
    __tablename__ = "payroll_run_employee"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    payroll_run_id: UUID = Field(foreign_key="payroll_run.id", index=True)
    person_id: str = Field(foreign_key="person.id", index=True)
    
    # Snapshot values (at time of payroll calculation)
    base_salary_amount: Optional[float] = Field(default=None, ge=0)
    
    # Calculated totals
    gross: float = Field(default=0, ge=0)
    deductions: float = Field(default=0, ge=0)
    net: float = Field(default=0)
    
    # Attendance summary
    total_hours: float = Field(default=0, ge=0)
    total_days: int = Field(default=0, ge=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    payroll_run: PayrollRun = Relationship(back_populates="employees")
    person: Person = Relationship()
    lines: List["PayrollRunLine"] = Relationship(back_populates="payroll_run_employee")


class PayrollRunLine(SQLModel, table=True):
    """Individual line items in employee payroll"""
    __tablename__ = "payroll_run_line"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    payroll_run_employee_id: UUID = Field(foreign_key="payroll_run_employee.id", index=True)
    component_id: Optional[UUID] = Field(default=None, foreign_key="salary_component.id")
    
    # Line details
    component_name_snapshot: Optional[str] = Field(default=None, max_length=100)  # Snapshot of component name
    kind: ComponentKind
    amount: float
    
    # Optional metadata (JSON stored as text)
    meta_json: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    payroll_run_employee: PayrollRunEmployee = Relationship(back_populates="lines")
    component: Optional[SalaryComponent] = Relationship(back_populates="payroll_lines")


# =============================================================================
# Salary Advance Model
# =============================================================================

class AdvanceStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REPAID = "repaid"
    CANCELLED = "cancelled"


class SalaryAdvance(SQLModel, table=True):
    """Salary advances tracking"""
    __tablename__ = "salary_advance"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    person_id: str = Field(foreign_key="person.id", index=True)
    component_id: UUID = Field(foreign_key="salary_component.id")
    repayment_component_id: Optional[UUID] = Field(default=None, foreign_key="employee_component.id")
    approved_by_person_id: Optional[str] = Field(default=None, foreign_key="person.id")
    
    # Advance data
    amount: float = Field(ge=0)  # Total advance amount
    taken_date: date = Field(index=True)  # When advance was taken
    remaining_balance: float = Field(ge=0)  # Updated after each payroll
    status: AdvanceStatus = Field(default=AdvanceStatus.PENDING)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    person: Person = Relationship(
        sa_relationship_kwargs={"foreign_keys": "SalaryAdvance.person_id"}
    )
    component: SalaryComponent = Relationship()
    approved_by: Optional[Person] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "SalaryAdvance.approved_by_person_id"}
    )


# =============================================================================
# Loan Model
# =============================================================================

class LoanStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Loan(SQLModel, table=True):
    """Loans tracking"""
    __tablename__ = "loan"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    person_id: str = Field(foreign_key="person.id", index=True)
    component_id: UUID = Field(foreign_key="salary_component.id")
    approved_by_person_id: Optional[str] = Field(default=None, foreign_key="person.id")
    
    # Loan data
    total_amount: float = Field(ge=0)
    remaining_balance: float = Field(ge=0)
    monthly_installment: float = Field(ge=0)
    start_date: date = Field(index=True)
    end_date: date
    status: LoanStatus = Field(default=LoanStatus.ACTIVE)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    person: Person = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Loan.person_id"}
    )
    component: SalaryComponent = Relationship()
    approved_by: Optional[Person] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Loan.approved_by_person_id"}
    )


# =============================================================================
# Payroll Group Model
# =============================================================================

class PayrollGroup(SQLModel, table=True):
    """Payroll groups for grouping employees"""
    __tablename__ = "payroll_group"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    name: str = Field(max_length=100, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    location_id: Optional[UUID] = Field(default=None, foreign_key="location.id")
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    location: Optional[Location] = Relationship()


# =============================================================================
# Payslip Model
# =============================================================================

class Payslip(SQLModel, table=True):
    """Generated payslips"""
    __tablename__ = "payslip"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign keys
    payroll_run_employee_id: UUID = Field(foreign_key="payroll_run_employee.id", index=True)
    person_id: str = Field(foreign_key="person.id", index=True)
    
    # Payslip data
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    pdf_url_ar: Optional[str] = Field(default=None, max_length=500)
    pdf_url_en: Optional[str] = Field(default=None, max_length=500)
    language: str = Field(default="ar", max_length=2)  # "ar" or "en"
    
    # Relationships
    payroll_run_employee: PayrollRunEmployee = Relationship()
    person: Person = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Payslip.person_id"}
    )


# =============================================================================
# Audit Log Model
# =============================================================================

class AuditLog(SQLModel, table=True):
    """Audit trail for all changes"""
    __tablename__ = "audit_log"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    table_name: str = Field(max_length=100, index=True)
    record_id: str = Field(max_length=100, index=True)
    action: str = Field(max_length=20)  # CREATE, UPDATE, DELETE
    changed_by_person_id: Optional[str] = Field(default=None, foreign_key="person.id", index=True)
    old_values: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON
    new_values: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    changed_by: Optional[Person] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "AuditLog.changed_by_person_id"}
    )


# Create indexes
Index("idx_attendance_person_date", Attendance.person_id, Attendance.attendance_date)
Index("idx_person_status", Person.status)
Index("idx_assignment_person", Assignment.person_id)
Index("idx_assignment_location", Assignment.location_id)
Index("idx_payroll_run_period", PayrollRun.payroll_period_id)
Index("idx_payroll_run_employee_person", PayrollRunEmployee.person_id)
