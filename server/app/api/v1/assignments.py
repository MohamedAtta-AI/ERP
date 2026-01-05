"""
Assignment API endpoints.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.app.database import get_session
from server.app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate
from server.db.models import Assignment, Person, Location, Shift

router = APIRouter()


@router.post("", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: AssignmentCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new assignment."""
    # Verify person, location, shift exist
    person_stmt = select(Person).where(Person.id == data.person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    location_stmt = select(Location).where(Location.id == data.location_id)
    location_result = await session.execute(location_stmt)
    location = location_result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    shift_stmt = select(Shift).where(Shift.id == data.shift_id)
    shift_result = await session.execute(shift_stmt)
    shift = shift_result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    assignment = Assignment(**data.model_dump())
    session.add(assignment)
    await session.flush()
    await session.refresh(assignment)
    
    return AssignmentRead(
        id=assignment.id,
        person_id=assignment.person_id,
        person_name=person.full_name,
        location_id=assignment.location_id,
        location_name=location.name,
        shift_id=assignment.shift_id,
        shift_name=shift.name,
        title=assignment.title,
        rate=assignment.rate,
        effective_from=assignment.effective_from,
        effective_to=assignment.effective_to,
        is_active=assignment.is_active,
        created_at=assignment.created_at,
    )


@router.get("", response_model=List[AssignmentRead])
async def list_assignments(
    person_id: str | None = None,
    location_id: UUID | None = None,
    active_only: bool = True,
    session: AsyncSession = Depends(get_session),
):
    """List assignments with optional filters."""
    stmt = select(Assignment, Person, Location, Shift).join(
        Person, Assignment.person_id == Person.id
    ).join(
        Location, Assignment.location_id == Location.id
    ).join(
        Shift, Assignment.shift_id == Shift.id
    )
    
    if person_id:
        stmt = stmt.where(Assignment.person_id == person_id)
    if location_id:
        stmt = stmt.where(Assignment.location_id == location_id)
    if active_only:
        stmt = stmt.where(Assignment.is_active == True)
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        AssignmentRead(
            id=assignment.id,
            person_id=assignment.person_id,
            person_name=person.full_name,
            location_id=assignment.location_id,
            location_name=location.name,
            shift_id=assignment.shift_id,
            shift_name=shift.name,
            title=assignment.title,
            rate=assignment.rate,
            effective_from=assignment.effective_from,
            effective_to=assignment.effective_to,
            is_active=assignment.is_active,
            created_at=assignment.created_at,
        )
        for assignment, person, location, shift in rows
    ]


@router.get("/{assignment_id}", response_model=AssignmentRead)
async def get_assignment(
    assignment_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get an assignment by ID."""
    stmt = select(Assignment, Person, Location, Shift).join(
        Person, Assignment.person_id == Person.id
    ).join(
        Location, Assignment.location_id == Location.id
    ).join(
        Shift, Assignment.shift_id == Shift.id
    ).where(Assignment.id == assignment_id)
    
    result = await session.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment, person, location, shift = row
    
    return AssignmentRead(
        id=assignment.id,
        person_id=assignment.person_id,
        person_name=person.full_name,
        location_id=assignment.location_id,
        location_name=location.name,
        shift_id=assignment.shift_id,
        shift_name=shift.name,
        title=assignment.title,
        rate=assignment.rate,
        effective_from=assignment.effective_from,
        effective_to=assignment.effective_to,
        is_active=assignment.is_active,
        created_at=assignment.created_at,
    )


@router.put("/{assignment_id}", response_model=AssignmentRead)
async def update_assignment(
    assignment_id: UUID,
    data: AssignmentUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update an assignment."""
    stmt = select(Assignment).where(Assignment.id == assignment_id)
    result = await session.execute(stmt)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # TODO: Apply field-level guard for rate/title (admin only)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    assignment.updated_at = __import__('datetime').datetime.utcnow()
    session.add(assignment)
    await session.flush()
    await session.refresh(assignment)
    
    # Get related data for response
    person_stmt = select(Person).where(Person.id == assignment.person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one()
    
    location_stmt = select(Location).where(Location.id == assignment.location_id)
    location_result = await session.execute(location_stmt)
    location = location_result.scalar_one()
    
    shift_stmt = select(Shift).where(Shift.id == assignment.shift_id)
    shift_result = await session.execute(shift_stmt)
    shift = shift_result.scalar_one()
    
    return AssignmentRead(
        id=assignment.id,
        person_id=assignment.person_id,
        person_name=person.full_name,
        location_id=assignment.location_id,
        location_name=location.name,
        shift_id=assignment.shift_id,
        shift_name=shift.name,
        title=assignment.title,
        rate=assignment.rate,
        effective_from=assignment.effective_from,
        effective_to=assignment.effective_to,
        is_active=assignment.is_active,
        created_at=assignment.created_at,
    )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete an assignment (soft delete)."""
    stmt = select(Assignment).where(Assignment.id == assignment_id)
    result = await session.execute(stmt)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment.is_active = False
    session.add(assignment)
    await session.flush()

