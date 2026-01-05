"""
Shift API endpoints.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.app.database import get_session
from server.app.schemas.shift import ShiftCreate, ShiftRead, ShiftUpdate
from server.db.models import Shift

router = APIRouter()


@router.post("", response_model=ShiftRead, status_code=status.HTTP_201_CREATED)
async def create_shift(
    data: ShiftCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new shift."""
    shift = Shift(**data.model_dump())
    session.add(shift)
    await session.flush()
    await session.refresh(shift)
    return ShiftRead.model_validate(shift)


@router.get("", response_model=List[ShiftRead])
async def list_shifts(
    active_only: bool = True,
    session: AsyncSession = Depends(get_session),
):
    """List all shifts."""
    stmt = select(Shift)
    if active_only:
        stmt = stmt.where(Shift.is_active == True)
    stmt = stmt.order_by(Shift.starts_at)
    
    result = await session.execute(stmt)
    shifts = result.scalars().all()
    return [ShiftRead.model_validate(s) for s in shifts]


@router.get("/{shift_id}", response_model=ShiftRead)
async def get_shift(
    shift_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a shift by ID."""
    stmt = select(Shift).where(Shift.id == shift_id)
    result = await session.execute(stmt)
    shift = result.scalar_one_or_none()
    
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    return ShiftRead.model_validate(shift)


@router.put("/{shift_id}", response_model=ShiftRead)
async def update_shift(
    shift_id: UUID,
    data: ShiftUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a shift."""
    stmt = select(Shift).where(Shift.id == shift_id)
    result = await session.execute(stmt)
    shift = result.scalar_one_or_none()
    
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shift, field, value)
    
    session.add(shift)
    await session.flush()
    await session.refresh(shift)
    
    return ShiftRead.model_validate(shift)


@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a shift (soft delete by setting is_active=False)."""
    stmt = select(Shift).where(Shift.id == shift_id)
    result = await session.execute(stmt)
    shift = result.scalar_one_or_none()
    
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    shift.is_active = False
    session.add(shift)
    await session.flush()

