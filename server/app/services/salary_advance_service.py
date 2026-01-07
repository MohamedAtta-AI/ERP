"""
Salary Advance Service

Handles salary advance creation, approval, and deduction calculations.
Enforces business rules: advances only between 10th-25th, max 30% of salary.
"""

from datetime import date
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from server.db.models import (
    Person, SalaryAdvance, AdvanceStatus, SalaryComponent, EmployeeComponent,
    ComponentType, ComponentKind, AmountType, Assignment
)


async def create_advance(
    person_id: str,
    amount: float,
    taken_date: date,
    session: AsyncSession,
) -> SalaryAdvance:
    """
    Create a salary advance with validation.
    
    Validates:
    - taken_date must be between 10th-25th of the month
    - amount must be <= 30% of person's base salary
    
    Creates:
    - SalaryAdvance record with status PENDING
    - EmployeeComponent for deduction (type ADVANCE_REPAYMENT)
    """
    # Validate date is between 10th-25th
    if not (10 <= taken_date.day <= 25):
        raise ValueError(
            f"Salary advance can only be taken between 10th-25th of the month. "
            f"Provided date: {taken_date.day}"
        )
    
    # Get person's base salary
    # First try to get from EmployeeComponent with BASE_SALARY type
    base_salary = 0.0
    
    # Get base salary component
    base_salary_stmt = select(SalaryComponent).where(
        SalaryComponent.type == ComponentType.BASE_SALARY,
        SalaryComponent.active == True
    )
    base_salary_result = await session.execute(base_salary_stmt)
    base_salary_component = base_salary_result.scalar_one_or_none()
    
    if base_salary_component:
        # Check for employee override
        emp_comp_stmt = select(EmployeeComponent).where(
            and_(
                EmployeeComponent.person_id == person_id,
                EmployeeComponent.component_id == base_salary_component.id
            )
        )
        emp_comp_result = await session.execute(emp_comp_stmt)
        emp_comp = emp_comp_result.scalar_one_or_none()
        
        if emp_comp and emp_comp.value_override:
            base_salary = emp_comp.value_override
        else:
            base_salary = base_salary_component.amount
    else:
        # Fallback to Assignment rate
        assignment_stmt = select(Assignment).where(
            and_(
                Assignment.person_id == person_id,
                Assignment.is_active == True
            )
        ).order_by(Assignment.effective_from.desc())
        assignment_result = await session.execute(assignment_stmt)
        assignment = assignment_result.scalar_one_or_none()
        
        if assignment and assignment.rate:
            base_salary = assignment.rate * 30  # Approximate monthly (daily rate * 30)
    
    # Validate 30% limit
    max_advance = base_salary * 0.30
    if amount > max_advance:
        raise ValueError(
            f"Advance amount ({amount}) exceeds 30% of base salary ({max_advance:.2f})"
        )
    
    # Get or create advance repayment component
    advance_component_stmt = select(SalaryComponent).where(
        and_(
            SalaryComponent.type == ComponentType.ADVANCE_REPAYMENT,
            SalaryComponent.active == True
        )
    )
    advance_component_result = await session.execute(advance_component_stmt)
    advance_component = advance_component_result.scalar_one_or_none()
    
    if not advance_component:
        # Create default advance repayment component
        advance_component = SalaryComponent(
            name="Salary Advance Repayment",
            kind=ComponentKind.DEDUCTION,
            type=ComponentType.ADVANCE_REPAYMENT,
            amount_type=AmountType.FIXED,
            amount=0,  # Will be set per advance
            active=True,
            taxable=False,
            insurable=False,
        )
        session.add(advance_component)
        await session.flush()
    
    # Create advance record
    advance = SalaryAdvance(
        person_id=person_id,
        component_id=advance_component.id,
        amount=amount,
        taken_date=taken_date,
        remaining_balance=amount,
        status=AdvanceStatus.PENDING,
    )
    session.add(advance)
    await session.flush()
    
    # Create EmployeeComponent for deduction
    # Calculate monthly repayment (spread over remaining month)
    days_in_month = 30  # Simplified
    days_remaining = days_in_month - taken_date.day + 1
    monthly_repayment = amount / max(days_remaining / 30, 1)  # At least 1 month
    
    repayment_component = EmployeeComponent(
        person_id=person_id,
        component_id=advance_component.id,
        value_override=monthly_repayment,
        effective_from=taken_date,
    )
    session.add(repayment_component)
    await session.flush()
    
    # Link repayment component to advance
    advance.repayment_component_id = repayment_component.id
    
    await session.refresh(advance)
    return advance


async def approve_advance(
    advance_id: UUID,
    approved_by_person_id: str,
    session: AsyncSession,
) -> SalaryAdvance:
    """
    Approve a salary advance.
    
    Updates status to APPROVED and sets approved_by_person_id.
    """
    stmt = select(SalaryAdvance).where(SalaryAdvance.id == advance_id)
    result = await session.execute(stmt)
    advance = result.scalar_one_or_none()
    
    if not advance:
        raise ValueError(f"Salary advance {advance_id} not found")
    
    if advance.status != AdvanceStatus.PENDING:
        raise ValueError(f"Advance is not pending (current status: {advance.status})")
    
    advance.status = AdvanceStatus.APPROVED
    advance.approved_by_person_id = approved_by_person_id
    
    session.add(advance)
    await session.flush()
    await session.refresh(advance)
    
    return advance


async def calculate_advance_deduction(
    person_id: str,
    period_start: date,
    period_end: date,
    session: AsyncSession,
) -> float:
    """
    Calculate total advance deduction for a payroll period.
    
    Gets all active (APPROVED) advances for the person and calculates
    the deduction amount (min of remaining_balance and monthly repayment).
    """
    # Get all approved advances that are not fully repaid
    stmt = select(SalaryAdvance).where(
        and_(
            SalaryAdvance.person_id == person_id,
            SalaryAdvance.status == AdvanceStatus.APPROVED,
            SalaryAdvance.remaining_balance > 0,
        )
    )
    result = await session.execute(stmt)
    advances = result.scalars().all()
    
    total_deduction = 0.0
    
    for advance in advances:
        # Get repayment component to get monthly repayment amount
        if advance.repayment_component_id:
            repayment_stmt = select(EmployeeComponent).where(
                EmployeeComponent.id == advance.repayment_component_id
            )
            repayment_result = await session.execute(repayment_stmt)
            repayment_comp = repayment_result.scalar_one_or_none()
            
            if repayment_comp and repayment_comp.value_override:
                monthly_repayment = repayment_comp.value_override
                # Deduct minimum of remaining balance and monthly repayment
                deduction = min(advance.remaining_balance, monthly_repayment)
                total_deduction += deduction
    
    return total_deduction


async def update_balance(
    advance_id: UUID,
    deduction_amount: float,
    session: AsyncSession,
) -> SalaryAdvance:
    """
    Update advance remaining balance after payroll deduction.
    
    Subtracts deduction_amount from remaining_balance.
    If remaining_balance <= 0, sets status to REPAID.
    """
    stmt = select(SalaryAdvance).where(SalaryAdvance.id == advance_id)
    result = await session.execute(stmt)
    advance = result.scalar_one_or_none()
    
    if not advance:
        raise ValueError(f"Salary advance {advance_id} not found")
    
    advance.remaining_balance = max(0, advance.remaining_balance - deduction_amount)
    
    if advance.remaining_balance <= 0:
        advance.status = AdvanceStatus.REPAID
    
    session.add(advance)
    await session.flush()
    await session.refresh(advance)
    
    return advance



