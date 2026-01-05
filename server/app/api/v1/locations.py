"""
Location API endpoints.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.app.database import get_session
from server.app.dependencies import require_role
from server.app.schemas.location import LocationCreate, LocationRead, LocationUpdate
from server.db.models import Location, Person

router = APIRouter()


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
async def create_location(
    data: LocationCreate,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new location (Admin only).
    
    Location = Client/Site. Includes contract_document_url and contract_name.
    """
    location = Location(**data.model_dump())
    session.add(location)
    await session.flush()
    await session.refresh(location)
    return LocationRead.model_validate(location)


@router.get("", response_model=List[LocationRead])
async def list_locations(
    active_only: bool = True,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """List all locations (Admin only)."""
    stmt = select(Location)
    if active_only:
        stmt = stmt.where(Location.is_active == True)
    stmt = stmt.order_by(Location.name)
    
    result = await session.execute(stmt)
    locations = result.scalars().all()
    return [LocationRead.model_validate(loc) for loc in locations]


@router.get("/{location_id}", response_model=LocationRead)
async def get_location(
    location_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Get a location by ID (Admin only)."""
    stmt = select(Location).where(Location.id == location_id)
    result = await session.execute(stmt)
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return LocationRead.model_validate(location)


@router.put("/{location_id}", response_model=LocationRead)
async def update_location(
    location_id: UUID,
    data: LocationUpdate,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Update a location (Admin only)."""
    stmt = select(Location).where(Location.id == location_id)
    result = await session.execute(stmt)
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)
    
    session.add(location)
    await session.flush()
    await session.refresh(location)
    
    return LocationRead.model_validate(location)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Delete a location (soft delete by setting is_active=False) (Admin only)."""
    stmt = select(Location).where(Location.id == location_id)
    result = await session.execute(stmt)
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location.is_active = False
    session.add(location)
    await session.flush()

