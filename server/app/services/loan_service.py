"""
Loan Service

Handles loan creation, approval, installment calculations, and balance updates.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from server.db.models import (
    Person, Loan, LoanStatus, SalaryComponent, EmployeeComponent,
    ComponentType, ComponentKind, AmountType
)


async def create_loan(
    person_id: str,
    total_amount: float,
    monthly_installment: float,
    start_date: date,
    end_date: date,
    session: AsyncSession,
) -> Loan:
    """
    Create a loan with repayment schedule.
    
    Creates:
    - Loan record with status ACTIVE
    - EmployeeComponent for deduction (type LOAN_INSTALLMENT)
    """
    # Get or create loan installment component
    loan_component_stmt = select(SalaryComponent).where(
        and_(
            SalaryComponent.type == ComponentType.LOAN_INSTALLMENT,
            SalaryComponent.active == True
        )
    )
    loan_component_result = await session.execute(loan_component_stmt)
    loan_component = loan_component_result.scalar_one_or_none()
    
    if not loan_component:
        # Create default loan installment component
        loan_component = SalaryComponent(
            name="Loan Installment",
            kind=ComponentKind.DEDUCTION,
            type=ComponentType.LOAN_INSTALLMENT,
            amount_type=AmountType.FIXED,
            amount=0,  # Will be set per loan
            active=True,
            taxable=False,
            insurable=False,
        )
        session.add(loan_component)
        await session.flush()
    
    # Create loan record
    loan = Loan(
        person_id=person_id,
        component_id=loan_component.id,
        total_amount=total_amount,
        remaining_balance=total_amount,
        monthly_installment=monthly_installment,
        start_date=start_date,
        end_date=end_date,
        status=LoanStatus.ACTIVE,
    )
    session.add(loan)
    await session.flush()
    
    # Create EmployeeComponent for deduction
    installment_component = EmployeeComponent(
        person_id=person_id,
        component_id=loan_component.id,
        value_override=monthly_installment,
        effective_from=start_date,
        effective_to=end_date,
    )
    session.add(installment_component)
    await session.flush()
    
    await session.refresh(loan)
    return loan


async def approve_loan(
    loan_id: UUID,
    approved_by_person_id: str,
    session: AsyncSession,
) -> Loan:
    """
    Approve a loan.
    
    Updates status to ACTIVE (if was PENDING) and sets approved_by_person_id.
    """
    stmt = select(Loan).where(Loan.id == loan_id)
    result = await session.execute(stmt)
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise ValueError(f"Loan {loan_id} not found")
    
    loan.status = LoanStatus.ACTIVE
    loan.approved_by_person_id = approved_by_person_id
    
    session.add(loan)
    await session.flush()
    await session.refresh(loan)
    
    return loan


async def calculate_installment(
    person_id: str,
    period_start: date,
    period_end: date,
    session: AsyncSession,
) -> float:
    """
    Calculate monthly installment deduction for a payroll period.
    
    Gets all active loans for the person and returns monthly_installment amount.
    """
    stmt = select(Loan).where(
        and_(
            Loan.person_id == person_id,
            Loan.status == LoanStatus.ACTIVE,
            Loan.remaining_balance > 0,
            # Loan should be active during this period
            Loan.start_date <= period_end,
            Loan.end_date >= period_start,
        )
    )
    result = await session.execute(stmt)
    loans = result.scalars().all()
    
    total_installment = sum(loan.monthly_installment for loan in loans)
    
    return total_installment


async def update_balance(
    loan_id: UUID,
    installment_amount: float,
    session: AsyncSession,
) -> Loan:
    """
    Update loan remaining balance after payroll deduction.
    
    Subtracts installment_amount from remaining_balance.
    If remaining_balance <= 0, sets status to COMPLETED.
    """
    stmt = select(Loan).where(Loan.id == loan_id)
    result = await session.execute(stmt)
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise ValueError(f"Loan {loan_id} not found")
    
    loan.remaining_balance = max(0, loan.remaining_balance - installment_amount)
    
    if loan.remaining_balance <= 0:
        loan.status = LoanStatus.COMPLETED
    
    session.add(loan)
    await session.flush()
    await session.refresh(loan)
    
    return loan


async def get_repayment_schedule(
    loan_id: UUID,
    session: AsyncSession,
) -> List[dict]:
    """
    Generate repayment schedule with dates and amounts.
    
    Returns list of scheduled payments with date and amount.
    """
    stmt = select(Loan).where(Loan.id == loan_id)
    result = await session.execute(stmt)
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise ValueError(f"Loan {loan_id} not found")
    
    schedule = []
    current_date = loan.start_date
    remaining = loan.total_amount
    installment_num = 1
    
    while current_date <= loan.end_date and remaining > 0:
        payment_amount = min(loan.monthly_installment, remaining)
        schedule.append({
            "installment_number": installment_num,
            "date": current_date,
            "amount": payment_amount,
            "remaining_balance": remaining - payment_amount,
        })
        remaining -= payment_amount
        installment_num += 1
        
        # Move to next month (simplified - add 30 days)
        from datetime import timedelta
        current_date = current_date + timedelta(days=30)
    
    return schedule

