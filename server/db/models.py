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
    """Work locations/sites"""
    __tablename__ = "location"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    city: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
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


# Create indexes
Index("idx_attendance_person_date", Attendance.person_id, Attendance.attendance_date)
Index("idx_person_status", Person.status)
