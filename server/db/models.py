from __future__ import annotations
from datetime import datetime, date, time
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, String, Date, DateTime, Column, Relationship, func
from pgvector.sqlalchemy import Vector
from .enums import *
from ..config import config


class PersonSkillLink(SQLModel, table=True):
    person_id: str | None = Field(default=None, primary_key=True, foreign_key="person.id", ondelete="CASCADE")
    skill_id: UUID | None = Field(default=None, primary_key=True, foreign_key="skill.id", ondelete="CASCADE")


class PersonSalaryComponentLink(SQLModel, table=True):
    person_id: str | None = Field(default=None, primary_key=True, foreign_key="person.id", ondelete="CASCADE")
    salary_component_id: UUID | None = Field(default=None, primary_key=True, foreign_key="salary_component.id", ondelete="CASCADE")


class SiteSkillLink(SQLModel, table=True):
    site_id: UUID | None = Field(default=None, primary_key=True, foreign_key="site.id", ondelete="CASCADE")
    skill_id: UUID | None = Field(default=None, primary_key=True, foreign_key="skill.id", ondelete="CASCADE")


class Person(SQLModel, table=True):
    id: str = Field(sa_column=Column(String(6), primary_key=True), min_length=6, max_length=6)
    password_hash: str = Field(min_length=5)
    full_name: str = Field(max_length=255, index=True)
    nationalID: str | None = Field(max_length=20, unique=True)
    passport: str | None = Field(max_length=9)
    phone: str = Field(max_length=15)
    email: str | None = Field(default=None)
    dob: date | None = Field(default=None)
    sex: str | None = Field(max_length=1)
    street_address: str | None = Field(default=None)
    region: str | None = Field(default=None)
    city: str | None = Field(default=None)
    role: Role
    hire_date: date = Field(sa_column=Column(Date, server_default=func.now()))
    termination_date: date | None = Field(default=None)
    status: PersonStatus = Field(default=PersonStatus.ACTIVE)
    pay_cycle: PayCycle | None = Field(default=None)
    worker_type: WorkerType | None = Field(default=None)
    overtime_eligible: bool = Field(default=True)
    incentive_eligible: bool = Field(default=True)

    face_embeddings: list["FaceEmbedding"] | None = Relationship(back_populates="person", cascade_delete=True)
    documents: list["Document"] | None = Relationship(back_populates="person", cascade_delete=True)
    payment_info: "PaymentInfo" | None = Relationship(back_populates="person", cascade_delete=True)
    skills: list["Skill"] | None = Relationship(back_populates="persons", link_model=PersonSkillLink)
    salary_components: list["SalaryComponent"] | None = Relationship(back_populates="persons", link_model=PersonSalaryComponentLink)
    attendances: list["Attendance"] | None = Relationship(back_populates="person", cascade_delete=True)
    assignments: list["Assignment"] | None = Relationship(back_populates="person", cascade_delete=True)


class FaceEmbedding(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(config.EMBEDDING_SIZE)))


    person_id: str | None = Field(foreign_key="person.id", ondelete="CASCADE")
    person: Person | None = Relationship(back_populates="face_embeddings")


class Document(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: DocType
    url: str

    person_id: str = Field(foreign_key="person.id", ondelete="CASCADE")
    person: Person = Relationship(back_populates="documents")


class PaymentInfo(SQLModel, table=True):
    payment_method: PaymentMethod
    bank_name: str | None = Field(default=None)
    account_holder: str | None = Field(default=None)
    account_number: str | None = Field(default=None)
    iban: str | None = Field(default=None)
    branch_code: str | None = Field(default=None)
    wallet_provider: str | None = Field(default=None)
    wallet_number: str | None = Field(default=None)

    person_id: str | None = Field(primary_key=True, foreign_key="person.id", ondelete="CASCADE")
    person: Person = Relationship(back_populates="payment_info")


class Skill(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    
    persons: list["Person"] = Relationship(back_populates="skills", link_model=PersonSkillLink)
    skill_values: list["SkillValue"] = Relationship(back_populates="skill")



class SalaryComponent(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str | None = Field(default=None)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now()))
    effective_from: date = Field(default_factory=date.today)
    effective_to: date | None = Field(default=None)
    amount: float = Field(default=0, ge=0)
    calculation_method: CalculationMethod
    type: ComponentType
    category: ComponentCategory

    persons: list["Person"] = Relationship(back_populates="salary_components", link_model=PersonSalaryComponentLink)
    skill_value: "SkillValue" = Relationship(back_populates="salary_component", cascade_delete=True)



class Site(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    street_address: str | None = Field(default=None)
    region: str | None = Field(default=None)
    city: str | None = Field(default=None)
    
    assignments: list["Assignment"] = Relationship(back_populates="site")
    skill_values: list["SkillValue"] = Relationship(back_populates="site")



class SkillValue(SQLModel, table=True):
    amount: float = Field(default=0, ge=0)

    site_id: UUID = Field(primary_key=True, foreign_key="site.id", ondelete="CASCADE")
    site: Site = Relationship(back_populates="skill_values")
    skill_id: UUID = Field(primary_key=True, foreign_key="skill.id", ondelete="CASCADE")
    skill: Skill = Relationship(back_populates="skill_values")
    salary_component_id: UUID = Field(primary_key=True, foreign_key="salary_component.id", ondelete="CASCADE")
    salary_component: SalaryComponent = Relationship(back_populates="skill_values")


class Shift(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    start_time: time
    end_time: time

    assignments: list["Assignment"] = Relationship(back_populates="shift")



class Attendance(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    date: date
    check_in: datetime
    check_out: datetime | None = Field(default=None)
    rate_snapshot: float = Field(default=0, ge=0)
    image_url: str | None = Field(default=None)
    
    person_id: str | None = Field(foreign_key="person.id", ondelete="CASCADE")
    person: Person = Relationship(back_populates="attendances")
    assignment_id: UUID | None = Field(foreign_key="assignment.id", ondelete="CASCADE")
    assignment: Assignment = Relationship(back_populates="attendances")

    overtime_request: OvertimeRequest = Relationship(back_populates="attendance")


class OvertimeRequest(SQLModel, table=True):
    hours: float = Field(default=0, ge=0)
    status: AttendanceStatus = Field(default=AttendanceStatus.OVERTIME_PENDING)
    notes: str | None = Field(default=None)

    attendance_id: UUID | None = Field(primary_key=True, foreign_key="attendance.id", ondelete="CASCADE")
    attendance: Attendance = Relationship(back_populates="overtime_request")


class Assignment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str | None = Field(default=None)
    effective_from: date = Field(default_factory=date.today)
    effective_to: date | None = Field(default=None)
    
    person_id: str | None = Field(foreign_key="person.id", ondelete="CASCADE")
    person: Person = Relationship(back_populates="assignments")
    site_id: UUID | None = Field(foreign_key="site.id", ondelete="CASCADE")
    site: Site = Relationship(back_populates="assignments")
    shift_id: UUID | None = Field(foreign_key="shift.id", ondelete="CASCADE")
    shift: Shift = Relationship(back_populates="assignments")

    attendances: list["Attendance"] = Relationship(back_populates="assignment")

