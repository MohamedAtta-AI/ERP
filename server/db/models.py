# from __future__ import annotations

from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID, uuid4

from sqlmodel import (
    SQLModel,
    Field,
    String,
    Date,
    DateTime,
    Column,
    Relationship,
    func,
    ForeignKey,
)
from pgvector.sqlalchemy import Vector

from .enums import *
from ..config import config


class PersonSkillLink(SQLModel, table=True):
    __tablename__ = "person_skill_link"

    person_id: Optional[str] = Field(
        default=None, primary_key=True, foreign_key="person.id", ondelete="CASCADE"
    )
    skill_id: Optional[UUID] = Field(
        default=None, primary_key=True, foreign_key="skill.id", ondelete="CASCADE"
    )


class PersonSalaryComponentLink(SQLModel, table=True):
    __tablename__ = "person_salary_component_link"

    person_id: Optional[str] = Field(
        default=None, primary_key=True, foreign_key="person.id", ondelete="CASCADE"
    )
    salary_component_id: Optional[UUID] = Field(
        default=None,
        primary_key=True,
        foreign_key="salary_component.id",
        ondelete="CASCADE",
    )


class SiteSkillLink(SQLModel, table=True):
    __tablename__ = "site_skill_link"

    site_id: Optional[UUID] = Field(
        default=None, primary_key=True, foreign_key="site.id", ondelete="CASCADE"
    )
    skill_id: Optional[UUID] = Field(
        default=None, primary_key=True, foreign_key="skill.id", ondelete="CASCADE"
    )


class Person(SQLModel, table=True):
    __tablename__ = "person"

    id: str = Field(
        sa_column=Column(String(6), primary_key=True), min_length=6, max_length=6
    )
    password_hash: str = Field(min_length=5)
    full_name: str = Field(max_length=255, index=True)
    nationalID: Optional[str] = Field(max_length=20, unique=True)
    passport: Optional[str] = Field(max_length=9)
    phone: str = Field(max_length=15)
    email: Optional[str] = Field(default=None)
    dob: Optional[date] = Field(default=None)
    sex: Optional[str] = Field(max_length=1)
    street_address: Optional[str] = Field(default=None)
    region: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    role: Role
    hire_date: date = Field(sa_column=Column(Date, server_default=func.now()))
    termination_date: Optional[date] = Field(default=None)
    status: PersonStatus = Field(default=PersonStatus.ACTIVE)
    pay_cycle: Optional["PayCycle"] = Field(default=None)
    worker_type: Optional["WorkerType"] = Field(default=None)
    overtime_eligible: bool = Field(default=True)
    incentive_eligible: bool = Field(default=True)

    # Self-referencing relationship
    supervisor_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(6),
            ForeignKey("person.id", ondelete="SET NULL"),
            index=True,
            nullable=True,
        ),
    )
    supervisor: Optional["Person"] = Relationship(
        back_populates="subordinates",
        sa_relationship_kwargs={"remote_side": "[Person.id]"},
    )
    subordinates: list["Person"] = Relationship(
        back_populates="supervisor",
    )

    # One-to-many relationships
    face_embeddings: list["FaceEmbedding"] = Relationship(
        back_populates="person", cascade_delete=True
    )
    documents: list["Document"] = Relationship(
        back_populates="person", cascade_delete=True
    )
    payment_info: Optional["PaymentInfo"] = Relationship(
        back_populates="person", cascade_delete=True
    )

    # Many-to-many relationships
    skills: list["Skill"] = Relationship(
        back_populates="persons", link_model=PersonSkillLink
    )
    salary_components: list["SalaryComponent"] = Relationship(
        back_populates="persons",
        link_model=PersonSalaryComponentLink,
    )

    # Other one-to-many relationships
    attendances: list["Attendance"] = Relationship(
        back_populates="person", cascade_delete=True
    )
    assignments: list["Assignment"] = Relationship(
        back_populates="person", cascade_delete=True
    )
    overtime_requests: list["OvertimeRequest"] = Relationship(
        back_populates="person", cascade_delete=True
    )


class FaceEmbedding(SQLModel, table=True):
    __tablename__ = "face_embedding"

    embedding: Optional[list["float"]] = Field(
        default=None, sa_column=Column(Vector(config.EMBEDDING_SIZE))
    )

    person_id: Optional[str] = Field(
        primary_key=True, foreign_key="person.id", ondelete="CASCADE"
    )
    person: Optional["Person"] = Relationship(back_populates="face_embeddings")


class Document(SQLModel, table=True):
    __tablename__ = "document"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: DocType
    url: str
    uploaded_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    person_id: str = Field(foreign_key="person.id", ondelete="CASCADE")
    person: Person = Relationship(back_populates="documents")


class PaymentInfo(SQLModel, table=True):
    __tablename__ = "payment_info"

    payment_method: PaymentMethod
    bank_name: Optional[str] = Field(default=None)
    account_holder: Optional[str] = Field(default=None)
    account_number: Optional[str] = Field(default=None)
    iban: Optional[str] = Field(default=None)
    branch_code: Optional[str] = Field(default=None)
    wallet_provider: Optional[WalletProvider] = Field(default=None)
    wallet_number: Optional[str] = Field(default=None)

    person_id: str = Field(
        primary_key=True, foreign_key="person.id", ondelete="CASCADE"
    )
    person: Person = Relationship(back_populates="payment_info")


class Skill(SQLModel, table=True):
    __tablename__ = "skill"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    rate: float = Field(default=0, ge=0)
    effective_from: date = Field(default_factory=date.today)
    effective_to: Optional[date] = Field(default=None)

    persons: list["Person"] = Relationship(
        back_populates="skills", link_model=PersonSkillLink
    )
    skill_values: list["SkillValue"] = Relationship(back_populates="skill")


class SalaryComponent(SQLModel, table=True):
    __tablename__ = "salary_component"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )
    effective_from: date = Field(default_factory=date.today)
    effective_to: Optional[date] = Field(default=None)
    amount: float = Field(default=0, ge=0)
    calculation_method: CalculationMethod
    type: ComponentType
    category: ComponentCategory

    persons: list["Person"] = Relationship(
        back_populates="salary_components", link_model=PersonSalaryComponentLink
    )


class Site(SQLModel, table=True):
    __tablename__ = "site"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    street_address: Optional[str] = Field(default=None)
    region: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)

    assignments: list["Assignment"] = Relationship(back_populates="site")
    skill_values: list["SkillValue"] = Relationship(back_populates="site")


class SkillValue(SQLModel, table=True):
    __tablename__ = "skill_value"

    amount: float = Field(default=0, ge=0)

    site_id: UUID = Field(primary_key=True, foreign_key="site.id", ondelete="CASCADE")
    site: Site = Relationship(back_populates="skill_values")

    skill_id: UUID = Field(primary_key=True, foreign_key="skill.id", ondelete="CASCADE")
    skill: Skill = Relationship(back_populates="skill_values")


class Shift(SQLModel, table=True):
    __tablename__ = "shift"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    start_time: time
    end_time: time

    assignments: list["Assignment"] = Relationship(back_populates="shift")


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    date: date
    check_in: datetime
    check_out: Optional[datetime] = Field(default=None)
    image_url: Optional[str] = Field(default=None)

    person_id: Optional[str] = Field(foreign_key="person.id", ondelete="CASCADE")
    person: Optional["Person"] = Relationship(back_populates="attendances")

    assignment_id: Optional[UUID] = Field(
        foreign_key="assignment.id", ondelete="CASCADE"
    )
    assignment: Optional["Assignment"] = Relationship(back_populates="attendances")

    overtime_request: Optional["OvertimeRequest"] = Relationship(
        back_populates="attendance"
    )


class OvertimeRequest(SQLModel, table=True):
    __tablename__ = "overtime_request"

    hours: float = Field(default=0, ge=0)
    status: AttendanceStatus = Field(default=AttendanceStatus.OVERTIME_PENDING)
    notes: Optional[str] = Field(default=None)

    person_id: Optional[str] = Field(foreign_key="person.id", ondelete="CASCADE")
    person: Optional["Person"] = Relationship(back_populates="overtime_requests")

    # PK must not be Optional
    attendance_id: UUID = Field(
        primary_key=True, foreign_key="attendance.id", ondelete="CASCADE"
    )
    attendance: Optional["Attendance"] = Relationship(back_populates="overtime_request")


class Assignment(SQLModel, table=True):
    __tablename__ = "assignment"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: Optional[str] = Field(default=None)
    effective_from: date = Field(default_factory=date.today)
    effective_to: Optional[date] = Field(default=None)
    rate: float = Field(default=0, ge=0)

    person_id: Optional[str] = Field(foreign_key="person.id", ondelete="CASCADE")
    person: Optional["Person"] = Relationship(back_populates="assignments")

    site_id: Optional[UUID] = Field(foreign_key="site.id", ondelete="CASCADE")
    site: Optional["Site"] = Relationship(back_populates="assignments")

    shift_id: Optional[UUID] = Field(foreign_key="shift.id", ondelete="CASCADE")
    shift: Optional["Shift"] = Relationship(back_populates="assignments")

    attendances: list["Attendance"] = Relationship(back_populates="assignment")
