"""
Payroll API endpoints.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.app.database import get_session
from server.app.schemas.payroll import (
    PayrollPeriodCreate, PayrollPeriodRead, PayrollPeriodUpdate,
    PayrollRunCreate, PayrollRunRead, PayrollRunUpdate, PayrollRunDetailRead,
    PayrollRunEmployeeRead, PayrollRunLineRead,
    SalaryComponentCreate, SalaryComponentRead, SalaryComponentUpdate,
)
from server.db.models import (
    PayrollPeriod, PayrollRun, PayrollRunEmployee, PayrollRunLine,
    PayrollPeriodStatus, PayrollRunStatus, Location,
    SalaryComponent, EmployeeComponent, Person,
)
from server.app.services.payroll_calculation import calculate_payroll

router = APIRouter()


# Payroll Period endpoints
@router.post("/periods", response_model=PayrollPeriodRead, status_code=status.HTTP_201_CREATED)
async def create_payroll_period(
    data: PayrollPeriodCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new payroll period."""
    period = PayrollPeriod(**data.model_dump())
    session.add(period)
    await session.flush()
    await session.refresh(period)
    return PayrollPeriodRead.model_validate(period)


@router.get("/periods", response_model=List[PayrollPeriodRead])
async def list_payroll_periods(
    session: AsyncSession = Depends(get_session),
):
    """List all payroll periods."""
    stmt = select(PayrollPeriod).order_by(PayrollPeriod.start_date.desc())
    result = await session.execute(stmt)
    periods = result.scalars().all()
    return [PayrollPeriodRead.model_validate(p) for p in periods]


@router.get("/periods/{period_id}", response_model=PayrollPeriodRead)
async def get_payroll_period(
    period_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a payroll period by ID."""
    stmt = select(PayrollPeriod).where(PayrollPeriod.id == period_id)
    result = await session.execute(stmt)
    period = result.scalar_one_or_none()
    
    if not period:
        raise HTTPException(status_code=404, detail="Payroll period not found")
    
    return PayrollPeriodRead.model_validate(period)


# Payroll Run endpoints
@router.post("/runs", response_model=PayrollRunRead, status_code=status.HTTP_201_CREATED)
async def create_payroll_run(
    data: PayrollRunCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create and calculate a new payroll run."""
    # Verify period exists
    period_stmt = select(PayrollPeriod).where(PayrollPeriod.id == data.payroll_period_id)
    period_result = await session.execute(period_stmt)
    period = period_result.scalar_one_or_none()
    
    if not period:
        raise HTTPException(status_code=404, detail="Payroll period not found")
    
    # Calculate payroll
    try:
        payroll_run = await calculate_payroll(
            data.payroll_period_id,
            data.location_id,
            session,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Get location name if provided
    location_name = None
    if payroll_run.location_id:
        loc_stmt = select(Location).where(Location.id == payroll_run.location_id)
        loc_result = await session.execute(loc_stmt)
        location = loc_result.scalar_one_or_none()
        if location:
            location_name = location.name
    
    return PayrollRunRead(
        id=payroll_run.id,
        payroll_period_id=payroll_run.payroll_period_id,
        location_id=payroll_run.location_id,
        location_name=location_name,
        status=payroll_run.status.value,
        notes=payroll_run.notes,
        created_by_person_id=payroll_run.created_by_person_id,
        approved_by_person_id=payroll_run.approved_by_person_id,
        created_at=payroll_run.created_at,
        approved_at=payroll_run.approved_at,
        updated_at=payroll_run.updated_at,
    )


@router.get("/runs", response_model=List[PayrollRunRead])
async def list_payroll_runs(
    period_id: UUID | None = None,
    location_id: UUID | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List payroll runs with optional filters."""
    stmt = select(PayrollRun, Location).outerjoin(
        Location, PayrollRun.location_id == Location.id
    )
    
    if period_id:
        stmt = stmt.where(PayrollRun.payroll_period_id == period_id)
    if location_id:
        stmt = stmt.where(PayrollRun.location_id == location_id)
    
    stmt = stmt.order_by(PayrollRun.created_at.desc())
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        PayrollRunRead(
            id=run.id,
            payroll_period_id=run.payroll_period_id,
            location_id=run.location_id,
            location_name=location.name if location else None,
            status=run.status.value,
            notes=run.notes,
            created_by_person_id=run.created_by_person_id,
            approved_by_person_id=run.approved_by_person_id,
            created_at=run.created_at,
            approved_at=run.approved_at,
            updated_at=run.updated_at,
        )
        for run, location in rows
    ]


@router.get("/runs/{run_id}", response_model=PayrollRunDetailRead)
async def get_payroll_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get detailed payroll run data including employee breakdown."""
    stmt = select(PayrollRun, Location).outerjoin(
        Location, PayrollRun.location_id == Location.id
    ).where(PayrollRun.id == run_id)
    
    result = await session.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    
    run, location = row
    
    # Get employees
    emp_stmt = select(PayrollRunEmployee, Person).join(
        Person, PayrollRunEmployee.person_id == Person.id
    ).where(PayrollRunEmployee.payroll_run_id == run_id)
    
    emp_result = await session.execute(emp_stmt)
    emp_rows = emp_result.all()
    
    employees = []
    for emp, person in emp_rows:
        # Get lines
        line_stmt = select(PayrollRunLine).where(
            PayrollRunLine.payroll_run_employee_id == emp.id
        )
        line_result = await session.execute(line_stmt)
        lines = [
            PayrollRunLineRead.model_validate(line)
            for line in line_result.scalars().all()
        ]
        
        employees.append(
            PayrollRunEmployeeRead(
                id=emp.id,
                person_id=emp.person_id,
                person_name=person.full_name,
                base_salary_amount=emp.base_salary_amount,
                gross=emp.gross,
                deductions=emp.deductions,
                net=emp.net,
                total_hours=emp.total_hours,
                total_days=emp.total_days,
                lines=lines,
            )
        )
    
    return PayrollRunDetailRead(
        id=run.id,
        payroll_period_id=run.payroll_period_id,
        location_id=run.location_id,
        location_name=location.name if location else None,
        status=run.status.value,
        notes=run.notes,
        created_at=run.created_at,
        employees=employees,
    )


@router.put("/runs/{run_id}", response_model=PayrollRunRead)
async def update_payroll_run(
    run_id: UUID,
    data: PayrollRunUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update payroll run (approve/lock)."""
    stmt = select(PayrollRun).where(PayrollRun.id == run_id)
    result = await session.execute(stmt)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Handle status changes
    if "status" in update_data:
        new_status = PayrollRunStatus(update_data["status"])
        if new_status == PayrollRunStatus.APPROVED and run.status == PayrollRunStatus.DRAFT:
            run.approved_at = datetime.utcnow()
        run.status = new_status
    
    if "notes" in update_data:
        run.notes = update_data["notes"]
    
    run.updated_at = datetime.utcnow()
    session.add(run)
    await session.flush()
    await session.refresh(run)
    
    # Get location name
    location_name = None
    if run.location_id:
        loc_stmt = select(Location).where(Location.id == run.location_id)
        loc_result = await session.execute(loc_stmt)
        location = loc_result.scalar_one_or_none()
        if location:
            location_name = location.name
    
    return PayrollRunRead(
        id=run.id,
        payroll_period_id=run.payroll_period_id,
        location_id=run.location_id,
        location_name=location_name,
        status=run.status.value,
        notes=run.notes,
        created_by_person_id=run.created_by_person_id,
        approved_by_person_id=run.approved_by_person_id,
        created_at=run.created_at,
        approved_at=run.approved_at,
        updated_at=run.updated_at,
    )


# Salary Component endpoints
@router.post("/components", response_model=SalaryComponentRead, status_code=status.HTTP_201_CREATED)
async def create_salary_component(
    data: SalaryComponentCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new salary component."""
    component = SalaryComponent(**data.model_dump())
    session.add(component)
    await session.flush()
    await session.refresh(component)
    return SalaryComponentRead.model_validate(component)


@router.get("/components", response_model=List[SalaryComponentRead])
async def list_salary_components(
    active_only: bool = True,
    session: AsyncSession = Depends(get_session),
):
    """List all salary components."""
    stmt = select(SalaryComponent)
    if active_only:
        stmt = stmt.where(SalaryComponent.active == True)
    stmt = stmt.order_by(SalaryComponent.name)
    
    result = await session.execute(stmt)
    components = result.scalars().all()
    return [SalaryComponentRead.model_validate(c) for c in components]


@router.get("/components/{component_id}", response_model=SalaryComponentRead)
async def get_salary_component(
    component_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a salary component by ID."""
    stmt = select(SalaryComponent).where(SalaryComponent.id == component_id)
    result = await session.execute(stmt)
    component = result.scalar_one_or_none()
    
    if not component:
        raise HTTPException(status_code=404, detail="Salary component not found")
    
    return SalaryComponentRead.model_validate(component)


@router.put("/components/{component_id}", response_model=SalaryComponentRead)
async def update_salary_component(
    component_id: UUID,
    data: SalaryComponentUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a salary component."""
    stmt = select(SalaryComponent).where(SalaryComponent.id == component_id)
    result = await session.execute(stmt)
    component = result.scalar_one_or_none()
    
    if not component:
        raise HTTPException(status_code=404, detail="Salary component not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(component, field, value)
    
    component.updated_at = datetime.utcnow()
    session.add(component)
    await session.flush()
    await session.refresh(component)
    
    return SalaryComponentRead.model_validate(component)


# Employee Component endpoints
from pydantic import BaseModel


class EmployeeComponentCreate(BaseModel):
    component_id: UUID
    value_override: float


class EmployeeComponentRead(BaseModel):
    id: UUID
    person_id: str
    component_id: UUID
    component_name: Optional[str] = None
    value_override: Optional[float] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    
    class Config:
        from_attributes = True


@router.get("/employee-components/{person_id}", response_model=List[EmployeeComponentRead])
async def get_employee_components(
    person_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get all salary component overrides for an employee."""
    # Verify person exists
    person_stmt = select(Person).where(Person.id == person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    stmt = select(EmployeeComponent, SalaryComponent).join(
        SalaryComponent, EmployeeComponent.component_id == SalaryComponent.id
    ).where(EmployeeComponent.person_id == person_id)
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        EmployeeComponentRead(
            id=ec.id,
            person_id=ec.person_id,
            component_id=ec.component_id,
            component_name=sc.name,
            value_override=ec.value_override,
            effective_from=ec.effective_from,
            effective_to=ec.effective_to,
        )
        for ec, sc in rows
    ]


@router.post("/employee-components/{person_id}", response_model=EmployeeComponentRead, status_code=status.HTTP_201_CREATED)
async def set_employee_component(
    person_id: str,
    data: EmployeeComponentCreate,
    session: AsyncSession = Depends(get_session),
):
    """Set or update a salary component override for an employee."""
    # Verify person exists
    person_stmt = select(Person).where(Person.id == person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Verify component exists
    comp_stmt = select(SalaryComponent).where(SalaryComponent.id == data.component_id)
    comp_result = await session.execute(comp_stmt)
    component = comp_result.scalar_one_or_none()
    
    if not component:
        raise HTTPException(status_code=404, detail="Salary component not found")
    
    # Check if override already exists
    existing_stmt = select(EmployeeComponent).where(
        EmployeeComponent.person_id == person_id,
        EmployeeComponent.component_id == data.component_id,
    )
    existing_result = await session.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        # Update existing
        existing.value_override = data.value_override
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        emp_comp = existing
    else:
        # Create new
        emp_comp = EmployeeComponent(
            person_id=person_id,
            component_id=data.component_id,
            value_override=data.value_override,
        )
        session.add(emp_comp)
    
    await session.flush()
    await session.refresh(emp_comp)
    
    return EmployeeComponentRead(
        id=emp_comp.id,
        person_id=emp_comp.person_id,
        component_id=emp_comp.component_id,
        component_name=component.name,
        value_override=emp_comp.value_override,
        effective_from=emp_comp.effective_from,
        effective_to=emp_comp.effective_to,
    )

