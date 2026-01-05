"""
Payroll API endpoints.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.app.database import get_session
from server.app.dependencies import require_role
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
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """List all payroll periods (Admin only)."""
    stmt = select(PayrollPeriod).order_by(PayrollPeriod.start_date.desc())
    result = await session.execute(stmt)
    periods = result.scalars().all()
    return [PayrollPeriodRead.model_validate(p) for p in periods]


@router.get("/periods/{period_id}", response_model=PayrollPeriodRead)
async def get_payroll_period(
    period_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Get a payroll period by ID (Admin only)."""
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
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    Create and calculate a new payroll run (Admin only).
    
    Calls calculate_payroll() service and returns PayrollRun with status DRAFT.
    """
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
            preview_mode=False,
        )
        
        # Set created_by
        payroll_run.created_by_person_id = current_user.id
        session.add(payroll_run)
        await session.flush()
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


@router.post("/runs/{run_id}/preview")
async def preview_payroll_run(
    run_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    Preview payroll before approval (Admin only).
    
    Calls calculate_payroll() with preview mode and returns calculated data without saving.
    """
    # Get existing run to get period and location
    stmt = select(PayrollRun).where(PayrollRun.id == run_id)
    result = await session.execute(stmt)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    
    # Calculate in preview mode
    try:
        preview_data = await calculate_payroll(
            run.payroll_period_id,
            run.location_id,
            session,
            preview_mode=True,
        )
        return preview_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/approve", response_model=PayrollRunRead)
async def approve_payroll_run(
    run_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    Approve payroll run (Admin only).
    
    Updates status to APPROVED, sets approved_by_person_id, and locks payroll run.
    """
    stmt = select(PayrollRun).where(PayrollRun.id == run_id)
    result = await session.execute(stmt)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    
    if run.status != PayrollRunStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve payroll run with status: {run.status.value}"
        )
    
    run.status = PayrollRunStatus.APPROVED
    run.approved_by_person_id = current_user.id
    run.approved_at = datetime.utcnow()
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


@router.post("/runs/{run_id}/lock", response_model=PayrollRunRead)
async def lock_payroll_run(
    run_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    Lock payroll run (Admin only).
    
    Updates status to LOCKED and prevents any modifications.
    """
    stmt = select(PayrollRun).where(PayrollRun.id == run_id)
    result = await session.execute(stmt)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    
    run.status = PayrollRunStatus.LOCKED
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


@router.post("/runs/{run_id}/retroactive")
async def create_retroactive_adjustment(
    run_id: UUID,
    person_id: str,
    component_id: UUID,
    amount: float,
    effective_from: Optional[date] = None,
    effective_to: Optional[date] = None,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    Create retroactive adjustment (Admin only).
    
    Creates adjustment payroll run for a specific person and component.
    """
    # Get original run
    stmt = select(PayrollRun).where(PayrollRun.id == run_id)
    result = await session.execute(stmt)
    original_run = result.scalar_one_or_none()
    
    if not original_run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    
    # Create adjustment run
    adjustment_run = PayrollRun(
        payroll_period_id=original_run.payroll_period_id,
        location_id=original_run.location_id,
        status=PayrollRunStatus.DRAFT,
        notes=f"Retroactive adjustment for person {person_id}, component {component_id}",
        created_by_person_id=current_user.id,
    )
    session.add(adjustment_run)
    await session.flush()
    
    # Create adjustment employee record
    adjustment_employee = PayrollRunEmployee(
        payroll_run_id=adjustment_run.id,
        person_id=person_id,
        gross=amount if amount > 0 else 0,
        deductions=abs(amount) if amount < 0 else 0,
        net=amount,
    )
    session.add(adjustment_employee)
    await session.flush()
    
    # Create adjustment line
    component_stmt = select(SalaryComponent).where(SalaryComponent.id == component_id)
    component_result = await session.execute(component_stmt)
    component = component_result.scalar_one_or_none()
    
    if component:
        adjustment_line = PayrollRunLine(
            payroll_run_employee_id=adjustment_employee.id,
            component_id=component_id,
            component_name_snapshot=component.name,
            kind=component.kind,
            amount=abs(amount),
        )
        session.add(adjustment_line)
    
    await session.flush()
    await session.refresh(adjustment_run)
    
    return {
        "adjustment_run_id": adjustment_run.id,
        "person_id": person_id,
        "component_id": component_id,
        "amount": amount,
        "message": "Retroactive adjustment created",
    }


@router.get("/runs", response_model=List[PayrollRunRead])
async def list_payroll_runs(
    period_id: UUID | None = None,
    location_id: UUID | None = None,
    status_filter: Optional[str] = None,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    List payroll runs with optional filters (Admin only).
    """
    stmt = select(PayrollRun, Location).outerjoin(
        Location, PayrollRun.location_id == Location.id
    )
    
    if period_id:
        stmt = stmt.where(PayrollRun.payroll_period_id == period_id)
    if location_id:
        stmt = stmt.where(PayrollRun.location_id == location_id)
    
    if status_filter:
        try:
            status_enum = PayrollRunStatus(status_filter)
            stmt = stmt.where(PayrollRun.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    
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
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Get detailed payroll run data including employee breakdown (Admin only)."""
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
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new salary component (Admin only).
    
    Includes metadata: taxable, insurable, max_amount, priority.
    """
    component = SalaryComponent(**data.model_dump())
    session.add(component)
    await session.flush()
    await session.refresh(component)
    return SalaryComponentRead.model_validate(component)


@router.get("/components", response_model=List[SalaryComponentRead])
async def list_salary_components(
    active_only: bool = True,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """List all salary components (Admin only)."""
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
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Get a salary component by ID (Admin only)."""
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
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a salary component (Admin only).
    """
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

