"""
Person/Employee API endpoints.

Handles person registration and face enrollment.
"""

import io
import numpy as np
from typing import Optional, List

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists

from server.app.database import get_session
from server.app.schemas.person import (
    PersonCreate,
    PersonRead,
    PersonUpdate,
    FaceEnrollResponse,
)
from server.app.services.person_id_generator import generate_person_id, validate_person_id
from server.db.models import Person, PersonStatus, Role
from server.services.face_recognition import FaceRecognitionService
from sqlalchemy.orm import selectinload

router = APIRouter()

# Initialize face recognition service
face_service = FaceRecognitionService()


async def check_id_exists(session: AsyncSession, person_id: str) -> bool:
    """Check if a person ID already exists in the database."""
    stmt = select(exists().where(Person.id == person_id))
    result = await session.execute(stmt)
    return result.scalar()


@router.post("/register", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
async def register_person(
    data: PersonCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Register a new person/employee.
    
    Generates a unique 6-character ID for the person.
    Face enrollment should be done separately via the enroll-face endpoint.
    """
    # Check for duplicate email if provided
    if data.email:
        stmt = select(exists().where(Person.email == data.email))
        result = await session.execute(stmt)
        if result.scalar():
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )
    
    # Check for duplicate identity number if provided
    if data.identity_number:
        stmt = select(exists().where(Person.identity_number == data.identity_number))
        result = await session.execute(stmt)
        if result.scalar():
            raise HTTPException(
                status_code=400,
                detail="Identity number already registered",
            )
    
    # Generate unique person ID
    async def id_exists_checker(pid: str) -> bool:
        return await check_id_exists(session, pid)
    
    # Generate ID (we need to check synchronously, so we'll retry in a loop)
    person_id = None
    for _ in range(100):
        candidate_id = generate_person_id()
        if not await check_id_exists(session, candidate_id):
            person_id = candidate_id
            break
    
    if not person_id:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate unique person ID",
        )
    
    # Create person
    person = Person(
        id=person_id,
        full_name=data.full_name,
        identity_number=data.identity_number,
        dob=data.dob,
        sex=data.sex,
        phone=data.phone,
        email=data.email,
        department=data.department,
        position=data.position,
        status=PersonStatus.ACTIVE,
    )
    
    session.add(person)
    await session.flush()  # Flush to get the ID and created_at timestamp
    await session.refresh(person)  # Refresh to get all fields from DB
    
    return PersonRead(
        person_id=person.id,
        full_name=person.full_name,
        identity_number=person.identity_number,
        dob=person.dob,
        sex=person.sex,
        phone=person.phone,
        email=person.email,
        department=person.department,
        position=person.position,
        status=person.status.value,
        has_face_enrolled=False,
        created_at=person.created_at,
    )


@router.get("/{person_id}", response_model=PersonRead)
async def get_person(
    person_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a person by their ID."""
    if not validate_person_id(person_id):
        raise HTTPException(status_code=400, detail="Invalid person ID format")
    
    # Load person with role relationship
    stmt = select(Person).options(selectinload(Person.role)).where(Person.id == person_id)
    result = await session.execute(stmt)
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Get role name from relationship
    role_name = person.role.name if person.role else None
    
    return PersonRead(
        person_id=person.id,
        full_name=person.full_name,
        identity_number=person.identity_number,
        dob=person.dob,
        sex=person.sex,
        phone=person.phone,
        email=person.email,
        department=person.department,
        position=person.position,
        status=person.status.value if isinstance(person.status, PersonStatus) else person.status,
        role=role_name,
        has_face_enrolled=person.face_embedding is not None,
        created_at=person.created_at,
    )


@router.post("/{person_id}/enroll-face", response_model=FaceEnrollResponse)
async def enroll_face(
    person_id: str,
    file: UploadFile = File(..., description="Face image for enrollment"),
    session: AsyncSession = Depends(get_session),
):
    """
    Enroll a face for a person.
    
    Generates face embedding and stores it for later verification.
    Replaces any existing face enrollment.
    """
    if not validate_person_id(person_id):
        raise HTTPException(status_code=400, detail="Invalid person ID format")
    
    # Verify person exists
    stmt = select(Person).where(Person.id == person_id)
    result = await session.execute(stmt)
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Read and validate image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
    
    # Convert to numpy array
    try:
        import cv2
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")
    
    # Generate embedding
    try:
        embedding, is_real = face_service.generate_embedding(image)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Optional: Reject enrollment if spoofing detected
    if is_real is False:
        raise HTTPException(
            status_code=400,
            detail="Spoofing detected. Please use a real face image for enrollment.",
        )
    
    # Store embedding
    person.face_embedding = embedding.tolist()
    person.updated_at = __import__('datetime').datetime.utcnow()
    session.add(person)
    
    return FaceEnrollResponse(
        person_id=person_id,
        message="Face enrolled successfully",
        embedding_size=len(embedding),
    )


@router.put("/{person_id}", response_model=PersonRead)
async def update_person(
    person_id: str,
    data: PersonUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a person's information."""
    if not validate_person_id(person_id):
        raise HTTPException(status_code=400, detail="Invalid person ID format")
    
    stmt = select(Person).where(Person.id == person_id)
    result = await session.execute(stmt)
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(person, field):
            setattr(person, field, value)
    
    person.updated_at = __import__('datetime').datetime.utcnow()
    session.add(person)
    await session.flush()
    
    return PersonRead(
        person_id=person.id,
        full_name=person.full_name,
        identity_number=person.identity_number,
        dob=person.dob,
        sex=person.sex,
        phone=person.phone,
        email=person.email,
        department=person.department,
        position=person.position,
        status=person.status.value if isinstance(person.status, PersonStatus) else person.status,
        has_face_enrolled=person.face_embedding is not None,
        created_at=person.created_at,
    )


@router.get("", response_model=List[PersonRead])
async def list_persons(
    status_filter: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """List all persons with optional filters."""
    stmt = select(Person).options(selectinload(Person.role))
    
    if status_filter:
        stmt = stmt.where(Person.status == status_filter)
    
    if role:
        stmt = stmt.join(Role).where(Role.name == role)
    
    stmt = stmt.order_by(Person.full_name).limit(limit)
    
    result = await session.execute(stmt)
    persons = result.scalars().all()
    
    return [
        PersonRead(
            person_id=person.id,
            full_name=person.full_name,
            identity_number=person.identity_number,
            dob=person.dob,
            sex=person.sex,
            phone=person.phone,
            email=person.email,
            department=person.department,
            position=person.position,
            status=person.status.value if isinstance(person.status, PersonStatus) else person.status,
            role=person.role.name if person.role else None,
            has_face_enrolled=person.face_embedding is not None,
            created_at=person.created_at,
        )
        for person in persons
    ]

