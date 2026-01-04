"""Employee model using SQLModel."""
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, DateTime, func
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .face_embedding import FaceEmbedding
    from .attendance import Attendance


class EmployeeBase(SQLModel):
    """Base employee model with shared fields."""
    employee_id: str = Field(max_length=6, sa_column=Column(String(6), unique=True, index=True))
    full_name: str = Field(max_length=255, sa_column=Column(String(255)))
    email: Optional[str] = Field(default=None, max_length=255, sa_column=Column(String(255), unique=True))
    department: Optional[str] = Field(default=None, max_length=100, sa_column=Column(String(100)))
    phone: Optional[str] = Field(default=None, max_length=20, sa_column=Column(String(20)))
    position: Optional[str] = Field(default=None, max_length=100, sa_column=Column(String(100)))


class Employee(EmployeeBase, table=True):
    """Employee database model."""
    __tablename__ = "employees"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
    
    # Relationships
    face_embeddings: List["FaceEmbedding"] = Relationship(
        back_populates="employee",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    attendance_records: List["Attendance"] = Relationship(
        back_populates="employee",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class EmployeeCreate(EmployeeBase):
    """Employee creation schema."""
    pass


class EmployeeResponse(EmployeeBase):
    """Employee response schema."""
    id: int
    created_at: datetime
