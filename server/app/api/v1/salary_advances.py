"""
Salary Advances API endpoints.

Admin only - handles salary advance creation, approval, and listing.
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
from server.app.services.salary_advance_service import (
    create_advance,
    approve_advance,
    calculate_advance_deduction,
)
from server.db.models import SalaryAdvance, AdvanceStatus, Person

router = APIRouter()


class SalaryAdvanceCreate(BaseModel):
    person_id: str
    amount: float
    taken_date: date


class SalaryAdvanceResponse(BaseModel):
    id: UUID
    person_id: str
    person_name: str
    amount: float
    taken_date: date
    remaining_balance: float
    status: str
    approved_by_person_id: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("", response_model=SalaryAdvanceResponse, status_code=status.HTTP_201_CREATED)
async def create_salary_advance(
    data: SalaryAdvanceCreate,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a salary advance.
    
    Validates:
    - taken_date must be between 10th-25th of the month
    - amount must be <= 30% of person's base salary
    
    Returns 400 if validation fails.
    """
    try:
        advance = await create_advance(
            data.person_id,
            data.amount,
            data.taken_date,
            session,
        )
        
        # Get person name
        person_stmt = select(Person).where(Person.id == data.person_id)
        person_result = await session.execute(person_stmt)
        person = person_result.scalar_one_or_none()
        person_name = person.full_name if person else "Unknown"
        
        return SalaryAdvanceResponse(
            id=advance.id,
            person_id=advance.person_id,
            person_name=person_name,
            amount=advance.amount,
            taken_date=advance.taken_date,
            remaining_balance=advance.remaining_balance,
            status=advance.status.value,
            approved_by_person_id=advance.approved_by_person_id,
            created_at=advance.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[SalaryAdvanceResponse])
async def list_salary_advances(
    person_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    List salary advances.
    
    Filters by person_id and status if provided.
    """
    stmt = select(SalaryAdvance)
    
    if person_id:
        stmt = stmt.where(SalaryAdvance.person_id == person_id)
    
    if status:
        try:
            status_enum = AdvanceStatus(status)
            stmt = stmt.where(SalaryAdvance.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    result = await session.execute(stmt)
    advances = result.scalars().all()
    
    # Get person names
    person_ids = {adv.person_id for adv in advances}
    persons = {}
    if person_ids:
        person_stmt = select(Person).where(Person.id.in_(person_ids))
        person_result = await session.execute(person_stmt)
        for person in person_result.scalars().all():
            persons[person.id] = person.full_name
    
    return [
        SalaryAdvanceResponse(
            id=adv.id,
            person_id=adv.person_id,
            person_name=persons.get(adv.person_id, "Unknown"),
            amount=adv.amount,
            taken_date=adv.taken_date,
            remaining_balance=adv.remaining_balance,
            status=adv.status.value,
            approved_by_person_id=adv.approved_by_person_id,
            created_at=adv.created_at.isoformat(),
        )
        for adv in advances
    ]


@router.get("/{advance_id}", response_model=SalaryAdvanceResponse)
async def get_salary_advance(
    advance_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Get salary advance details."""
    stmt = select(SalaryAdvance).where(SalaryAdvance.id == advance_id)
    result = await session.execute(stmt)
    advance = result.scalar_one_or_none()
    
    if not advance:
        raise HTTPException(status_code=404, detail="Salary advance not found")
    
    # Get person name
    person_stmt = select(Person).where(Person.id == advance.person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    person_name = person.full_name if person else "Unknown"
    
    return SalaryAdvanceResponse(
        id=advance.id,
        person_id=advance.person_id,
        person_name=person_name,
        amount=advance.amount,
        taken_date=advance.taken_date,
        remaining_balance=advance.remaining_balance,
        status=advance.status.value,
        approved_by_person_id=advance.approved_by_person_id,
        created_at=advance.created_at.isoformat(),
    )


@router.put("/{advance_id}/approve", response_model=SalaryAdvanceResponse)
async def approve_salary_advance(
    advance_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Approve a salary advance."""
    try:
        advance = await approve_advance(advance_id, current_user.id, session)
        
        # Get person name
        person_stmt = select(Person).where(Person.id == advance.person_id)
        person_result = await session.execute(person_stmt)
        person = person_result.scalar_one_or_none()
        person_name = person.full_name if person else "Unknown"
        
        return SalaryAdvanceResponse(
            id=advance.id,
            person_id=advance.person_id,
            person_name=person_name,
            amount=advance.amount,
            taken_date=advance.taken_date,
            remaining_balance=advance.remaining_balance,
            status=advance.status.value,
            approved_by_person_id=advance.approved_by_person_id,
            created_at=advance.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

