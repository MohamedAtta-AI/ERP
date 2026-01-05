"""
Skills API endpoints.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.app.database import get_session
from server.app.schemas.skill import (
    SkillCreate, SkillRead, SkillUpdate,
    PersonSkillCreate, PersonSkillRead,
    SkillLocationPriceCreate, SkillLocationPriceRead,
)
from server.db.models import Skill, PersonSkill, SkillLocationPrice, Person, Location

router = APIRouter()


# Skill CRUD
@router.post("", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
async def create_skill(
    data: SkillCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new skill."""
    skill = Skill(**data.model_dump())
    session.add(skill)
    await session.flush()
    await session.refresh(skill)
    return SkillRead.model_validate(skill)


@router.get("", response_model=List[SkillRead])
async def list_skills(
    active_only: bool = True,
    session: AsyncSession = Depends(get_session),
):
    """List all skills."""
    stmt = select(Skill)
    if active_only:
        stmt = stmt.where(Skill.is_active == True)
    stmt = stmt.order_by(Skill.name)
    
    result = await session.execute(stmt)
    skills = result.scalars().all()
    return [SkillRead.model_validate(s) for s in skills]


@router.get("/{skill_id}", response_model=SkillRead)
async def get_skill(
    skill_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a skill by ID."""
    stmt = select(Skill).where(Skill.id == skill_id)
    result = await session.execute(stmt)
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return SkillRead.model_validate(skill)


@router.put("/{skill_id}", response_model=SkillRead)
async def update_skill(
    skill_id: UUID,
    data: SkillUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a skill."""
    stmt = select(Skill).where(Skill.id == skill_id)
    result = await session.execute(stmt)
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(skill, field, value)
    
    session.add(skill)
    await session.flush()
    await session.refresh(skill)
    
    return SkillRead.model_validate(skill)


# Person-Skill relationships
@router.post("/assign", response_model=PersonSkillRead, status_code=status.HTTP_201_CREATED)
async def assign_skill_to_person(
    data: PersonSkillCreate,
    session: AsyncSession = Depends(get_session),
):
    """Assign a skill to a person."""
    # Verify person exists
    person_stmt = select(Person).where(Person.id == data.person_id)
    person_result = await session.execute(person_stmt)
    if not person_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Verify skill exists
    skill_stmt = select(Skill).where(Skill.id == data.skill_id)
    skill_result = await session.execute(skill_stmt)
    skill = skill_result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Check if already assigned
    existing_stmt = select(PersonSkill).where(
        PersonSkill.person_id == data.person_id,
        PersonSkill.skill_id == data.skill_id,
    )
    existing_result = await session.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Skill already assigned to person")
    
    person_skill = PersonSkill(**data.model_dump())
    session.add(person_skill)
    await session.flush()
    
    return PersonSkillRead(
        person_id=person_skill.person_id,
        skill_id=person_skill.skill_id,
        skill_name=skill.name,
        certified_at=person_skill.certified_at,
        expires_at=person_skill.expires_at,
        created_at=person_skill.created_at,
    )


@router.get("/person/{person_id}", response_model=List[PersonSkillRead])
async def get_person_skills(
    person_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get all skills assigned to a person."""
    stmt = select(PersonSkill, Skill).join(
        Skill, PersonSkill.skill_id == Skill.id
    ).where(PersonSkill.person_id == person_id)
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        PersonSkillRead(
            person_id=ps.person_id,
            skill_id=ps.skill_id,
            skill_name=s.name,
            certified_at=ps.certified_at,
            expires_at=ps.expires_at,
            created_at=ps.created_at,
        )
        for ps, s in rows
    ]


# Skill-Location pricing
@router.post("/pricing", response_model=SkillLocationPriceRead, status_code=status.HTTP_201_CREATED)
async def create_skill_location_price(
    data: SkillLocationPriceCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create or update skill-location pricing."""
    # Verify skill and location exist
    skill_stmt = select(Skill).where(Skill.id == data.skill_id)
    skill_result = await session.execute(skill_stmt)
    skill = skill_result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    location_stmt = select(Location).where(Location.id == data.location_id)
    location_result = await session.execute(location_stmt)
    location = location_result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if pricing exists
    existing_stmt = select(SkillLocationPrice).where(
        SkillLocationPrice.skill_id == data.skill_id,
        SkillLocationPrice.location_id == data.location_id,
    )
    existing_result = await session.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        # Update existing
        for field, value in data.model_dump(exclude={"skill_id", "location_id"}).items():
            setattr(existing, field, value)
        existing.updated_at = __import__('datetime').datetime.utcnow()
        session.add(existing)
        await session.flush()
        price = existing
    else:
        # Create new
        price = SkillLocationPrice(**data.model_dump())
        session.add(price)
        await session.flush()
    
    return SkillLocationPriceRead(
        skill_id=price.skill_id,
        location_id=price.location_id,
        skill_name=skill.name,
        location_name=location.name,
        price=price.price,
        currency=price.currency,
        effective_from=price.effective_from,
        effective_to=price.effective_to,
        created_at=price.created_at,
    )


@router.get("/pricing", response_model=List[SkillLocationPriceRead])
async def list_skill_location_prices(
    skill_id: UUID | None = None,
    location_id: UUID | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List skill-location prices."""
    stmt = select(SkillLocationPrice, Skill, Location).join(
        Skill, SkillLocationPrice.skill_id == Skill.id
    ).join(
        Location, SkillLocationPrice.location_id == Location.id
    )
    
    if skill_id:
        stmt = stmt.where(SkillLocationPrice.skill_id == skill_id)
    if location_id:
        stmt = stmt.where(SkillLocationPrice.location_id == location_id)
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        SkillLocationPriceRead(
            skill_id=price.skill_id,
            location_id=price.location_id,
            skill_name=skill.name,
            location_name=location.name,
            price=price.price,
            currency=price.currency,
            effective_from=price.effective_from,
            effective_to=price.effective_to,
            created_at=price.created_at,
        )
        for price, skill, location in rows
    ]

