"""
Loans API endpoints.

Admin only - handles loan creation, approval, and listing.
"""

from datetime import date
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from server.app.database import get_session
from server.app.dependencies import require_auth, require_role
from server.app.services.loan_service import (
    create_loan,
    approve_loan,
    get_repayment_schedule,
)
from server.db.models import Loan, LoanStatus, Person

router = APIRouter()


class LoanCreate(BaseModel):
    person_id: str
    total_amount: float
    monthly_installment: float
    start_date: date
    end_date: date


class LoanResponse(BaseModel):
    id: UUID
    person_id: str
    person_name: str
    total_amount: float
    remaining_balance: float
    monthly_installment: float
    start_date: date
    end_date: date
    status: str
    approved_by_person_id: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class RepaymentScheduleItem(BaseModel):
    installment_number: int
    date: date
    amount: float
    remaining_balance: float


@router.post("", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def create_loan(
    data: LoanCreate,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Create a loan."""
    try:
        loan = await create_loan(
            data.person_id,
            data.total_amount,
            data.monthly_installment,
            data.start_date,
            data.end_date,
            session,
        )
        
        # Get person name
        person_stmt = select(Person).where(Person.id == data.person_id)
        person_result = await session.execute(person_stmt)
        person = person_result.scalar_one_or_none()
        person_name = person.full_name if person else "Unknown"
        
        return LoanResponse(
            id=loan.id,
            person_id=loan.person_id,
            person_name=person_name,
            total_amount=loan.total_amount,
            remaining_balance=loan.remaining_balance,
            monthly_installment=loan.monthly_installment,
            start_date=loan.start_date,
            end_date=loan.end_date,
            status=loan.status.value,
            approved_by_person_id=loan.approved_by_person_id,
            created_at=loan.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[LoanResponse])
async def list_loans(
    person_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """List loans with optional filters."""
    stmt = select(Loan)
    
    if person_id:
        stmt = stmt.where(Loan.person_id == person_id)
    
    if status:
        try:
            status_enum = LoanStatus(status)
            stmt = stmt.where(Loan.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    result = await session.execute(stmt)
    loans = result.scalars().all()
    
    # Get person names
    person_ids = {loan.person_id for loan in loans}
    persons = {}
    if person_ids:
        person_stmt = select(Person).where(Person.id.in_(person_ids))
        person_result = await session.execute(person_stmt)
        for person in person_result.scalars().all():
            persons[person.id] = person.full_name
    
    return [
        LoanResponse(
            id=loan.id,
            person_id=loan.person_id,
            person_name=persons.get(loan.person_id, "Unknown"),
            total_amount=loan.total_amount,
            remaining_balance=loan.remaining_balance,
            monthly_installment=loan.monthly_installment,
            start_date=loan.start_date,
            end_date=loan.end_date,
            status=loan.status.value,
            approved_by_person_id=loan.approved_by_person_id,
            created_at=loan.created_at.isoformat(),
        )
        for loan in loans
    ]


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Get loan details."""
    stmt = select(Loan).where(Loan.id == loan_id)
    result = await session.execute(stmt)
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Get person name
    person_stmt = select(Person).where(Person.id == loan.person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    person_name = person.full_name if person else "Unknown"
    
    return LoanResponse(
        id=loan.id,
        person_id=loan.person_id,
        person_name=person_name,
        total_amount=loan.total_amount,
        remaining_balance=loan.remaining_balance,
        monthly_installment=loan.monthly_installment,
        start_date=loan.start_date,
        end_date=loan.end_date,
        status=loan.status.value,
        approved_by_person_id=loan.approved_by_person_id,
        created_at=loan.created_at.isoformat(),
    )


@router.get("/{loan_id}/schedule", response_model=List[RepaymentScheduleItem])
async def get_loan_schedule(
    loan_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Get loan repayment schedule."""
    try:
        schedule = await get_repayment_schedule(loan_id, session)
        return [
            RepaymentScheduleItem(
                installment_number=item["installment_number"],
                date=item["date"],
                amount=item["amount"],
                remaining_balance=item["remaining_balance"],
            )
            for item in schedule
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{loan_id}/approve", response_model=LoanResponse)
async def approve_loan_endpoint(
    loan_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Approve a loan."""
    try:
        loan = await approve_loan(loan_id, current_user.id, session)
        
        # Get person name
        person_stmt = select(Person).where(Person.id == loan.person_id)
        person_result = await session.execute(person_stmt)
        person = person_result.scalar_one_or_none()
        person_name = person.full_name if person else "Unknown"
        
        return LoanResponse(
            id=loan.id,
            person_id=loan.person_id,
            person_name=person_name,
            total_amount=loan.total_amount,
            remaining_balance=loan.remaining_balance,
            monthly_installment=loan.monthly_installment,
            start_date=loan.start_date,
            end_date=loan.end_date,
            status=loan.status.value,
            approved_by_person_id=loan.approved_by_person_id,
            created_at=loan.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



