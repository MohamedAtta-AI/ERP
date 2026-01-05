"""
Final Settlement Service

Handles final settlement calculations for terminations/resignations.
"""

from datetime import date
from typing import Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from server.db.models import (
    Person, PayrollPeriod, PayrollRun, PayrollRunEmployee, PayrollRunStatus,
    SalaryAdvance, Loan, AdvanceStatus, LoanStatus
)
from server.app.services.loan_service import calculate_installment


async def calculate_settlement(
    person_id: str,
    termination_date: date,
    session: AsyncSession,
) -> Dict:
    """
    Calculate final settlement for termination.
    
    Includes:
    - Pro-rata salary for current month
    - Unused leave payout (if applicable)
    - Deducts outstanding loans and advances
    
    Returns settlement breakdown dictionary.
    """
    # Get person
    person_stmt = select(Person).where(Person.id == person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    
    if not person:
        raise ValueError(f"Person {person_id} not found")
    
    # Calculate pro-rata salary
    # Get current month's base salary
    pro_rata_salary = await _calculate_pro_rata_salary(
        person_id, termination_date, session
    )
    
    # Include unused leave payout
    unused_leave_payout = await include_unused_leave(
        person_id, termination_date, session
    )
    
    # Deduct outstanding liabilities
    total_liabilities = await deduct_outstanding_liabilities(
        person_id, session
    )
    
    # Calculate net settlement
    gross_settlement = pro_rata_salary + unused_leave_payout
    net_settlement = gross_settlement - total_liabilities
    
    return {
        "person_id": person_id,
        "termination_date": termination_date,
        "pro_rata_salary": pro_rata_salary,
        "unused_leave_payout": unused_leave_payout,
        "outstanding_liabilities": total_liabilities,
        "gross_settlement": gross_settlement,
        "net_settlement": net_settlement,
    }


async def include_unused_leave(
    person_id: str,
    termination_date: date,
    session: AsyncSession,
) -> float:
    """
    Calculate unused leave payout.
    
    Calculates accrued but unused leave days and applies daily rate.
    Returns payout amount.
    """
    # Simplified: Assume 21 days annual leave, calculate accrued days
    # This should be replaced with actual leave tracking system
    days_per_year = 21
    days_per_month = days_per_year / 12
    
    # Get person's hire date
    person_stmt = select(Person).where(Person.id == person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    
    if not person or not person.hire_date:
        return 0.0
    
    # Calculate months worked
    months_worked = (termination_date.year - person.hire_date.year) * 12 + \
                    (termination_date.month - person.hire_date.month)
    
    # Calculate accrued leave days (simplified)
    accrued_days = months_worked * days_per_month
    
    # Get daily rate (base salary / 30)
    # This should get from actual salary components
    daily_rate = 0.0  # Placeholder - should calculate from base salary
    
    payout = accrued_days * daily_rate
    return payout


async def deduct_outstanding_liabilities(
    person_id: str,
    session: AsyncSession,
) -> float:
    """
    Sum all outstanding loans and advances.
    
    Returns total liabilities amount.
    """
    # Get active loans
    loan_stmt = select(func.sum(Loan.remaining_balance)).where(
        and_(
            Loan.person_id == person_id,
            Loan.status == LoanStatus.ACTIVE,
            Loan.remaining_balance > 0,
        )
    )
    loan_result = await session.execute(loan_stmt)
    loan_total = loan_result.scalar() or 0.0
    
    # Get active advances
    advance_stmt = select(func.sum(SalaryAdvance.remaining_balance)).where(
        and_(
            SalaryAdvance.person_id == person_id,
            SalaryAdvance.status == AdvanceStatus.APPROVED,
            SalaryAdvance.remaining_balance > 0,
        )
    )
    advance_result = await session.execute(advance_stmt)
    advance_total = advance_result.scalar() or 0.0
    
    return loan_total + advance_total


async def require_clearance(
    person_id: str,
    session: AsyncSession,
) -> Dict:
    """
    Check if person has outstanding liabilities or pending approvals.
    
    Returns clearance status dictionary.
    """
    liabilities = await deduct_outstanding_liabilities(person_id, session)
    
    # Check for pending approvals (simplified - can be extended)
    has_pending_approvals = False  # Placeholder
    
    is_clear = liabilities == 0 and not has_pending_approvals
    
    return {
        "is_clear": is_clear,
        "outstanding_liabilities": liabilities,
        "has_pending_approvals": has_pending_approvals,
    }


async def generate_settlement_payroll(
    person_id: str,
    settlement_data: Dict,
    session: AsyncSession,
) -> PayrollRun:
    """
    Create special PayrollRun for settlement.
    
    Creates PayrollRun with settlement amounts.
    """
    # Create a special payroll period for settlement
    # Or use current period
    period_stmt = select(PayrollPeriod).order_by(
        PayrollPeriod.start_date.desc()
    ).limit(1)
    period_result = await session.execute(period_stmt)
    period = period_result.scalar_one_or_none()
    
    if not period:
        raise ValueError("No payroll period found")
    
    # Create settlement payroll run
    settlement_run = PayrollRun(
        payroll_period_id=period.id,
        location_id=None,  # Settlement is not location-specific
        status=PayrollRunStatus.DRAFT,
        notes=f"Final settlement for person {person_id}",
    )
    session.add(settlement_run)
    await session.flush()
    
    # Create PayrollRunEmployee with settlement amounts
    settlement_employee = PayrollRunEmployee(
        payroll_run_id=settlement_run.id,
        person_id=person_id,
        base_salary_amount=settlement_data.get("pro_rata_salary", 0),
        gross=settlement_data.get("gross_settlement", 0),
        deductions=settlement_data.get("outstanding_liabilities", 0),
        net=settlement_data.get("net_settlement", 0),
        total_hours=0,
        total_days=0,
    )
    session.add(settlement_employee)
    await session.flush()
    
    await session.refresh(settlement_run)
    return settlement_run


async def _calculate_pro_rata_salary(
    person_id: str,
    termination_date: date,
    session: AsyncSession,
) -> float:
    """
    Calculate pro-rata salary for partial month.
    
    Helper function to calculate salary for days worked in current month.
    """
    # Get base salary (simplified)
    # This should get from EmployeeComponent or Assignment
    base_salary = 0.0  # Placeholder
    
    # Calculate days worked in month
    days_in_month = 30  # Simplified
    days_worked = termination_date.day
    
    pro_rata = (base_salary / days_in_month) * days_worked
    return pro_rata

