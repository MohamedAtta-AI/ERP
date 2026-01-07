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
from server.app.dependencies import require_auth, require_role, get_user_role, field_level_guard
from server.app.schemas.person import (
    PersonCreate,
    PersonRead,
    PersonUpdate,
    FaceEnrollResponse,
)
from server.app.services.person_id_generator import generate_person_id, validate_person_id
from server.app.services.password_service import hash_password
from server.app.services.audit_service import log_change
from server.app.middleware.rbac import filter_admin_only_fields, ADMIN_ONLY_FIELDS
from server.db.models import (
    Person, PersonStatus, Role, EmploymentStatus, WorkerType, ContractType,
    PayCycle, InsuranceStatus, PaymentMethod, PaymentStatus
)
from server.app.services.face_recognition import FaceRecognitionService
from sqlalchemy.orm import selectinload

router = APIRouter()

# Admin-only fields for Person
PERSON_ADMIN_ONLY_FIELDS = [
    "rate", "salary", "position", "department", "payment_method",
    "bank_name", "iban", "account_number", "account_holder_name",
    "branch_code", "wallet_provider", "wallet_number", "payroll_currency",
    "payment_status", "role_id", "payroll_group_id"
]

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
    current_user: Person = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """
    Register a new person/employee.
    
    Admin: Can create any person with all fields.
    Supervisor: Can create workers only, non-monetary fields only.
    Generates a unique 6-character ID for the person.
    Face enrollment should be done separately via the enroll-face endpoint.
    """
    # Get user role
    role_name = await get_user_role(current_user, session)
    
    # Supervisor can only create workers
    if role_name == "supervisor":
        # Get worker role
        worker_role_stmt = select(Role).where(Role.name == "worker")
        worker_role_result = await session.execute(worker_role_stmt)
        worker_role = worker_role_result.scalar_one_or_none()
        
        if not worker_role:
            raise HTTPException(
                status_code=400,
                detail="Worker role not found. Contact admin."
            )
        
        # Force role to worker
        data.role_id = str(worker_role.id)
        
        # Filter admin-only fields
        update_data = data.model_dump(exclude_unset=True)
        filtered_data = filter_admin_only_fields(
            update_data, PERSON_ADMIN_ONLY_FIELDS, role_name
        )
        data = PersonCreate(**filtered_data)
    
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
    
    # Hash password if provided
    password_hash = None
    if data.password:
        password_hash = hash_password(data.password)
    
    # Create person with all fields
    person_data = data.model_dump(exclude={"password", "role_id"})
    if password_hash:
        person_data["password_hash"] = password_hash
    
    # Convert string enums to enum values
    if person_data.get("employment_status"):
        person_data["employment_status"] = EmploymentStatus(person_data["employment_status"])
    if person_data.get("worker_type"):
        person_data["worker_type"] = WorkerType(person_data["worker_type"])
    if person_data.get("contract_type"):
        person_data["contract_type"] = ContractType(person_data["contract_type"])
    if person_data.get("pay_cycle"):
        person_data["pay_cycle"] = PayCycle(person_data["pay_cycle"])
    if person_data.get("insurance_enrollment_status"):
        person_data["insurance_enrollment_status"] = InsuranceStatus(person_data["insurance_enrollment_status"])
    if person_data.get("payment_method"):
        person_data["payment_method"] = PaymentMethod(person_data["payment_method"])
    if person_data.get("payment_status"):
        person_data["payment_status"] = PaymentStatus(person_data["payment_status"])
    
    # Set role_id if provided (convert UUID string to UUID)
    if data.role_id:
        from uuid import UUID
        try:
            person_data["role_id"] = UUID(data.role_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role_id format")
    
    person = Person(
        id=person_id,
        status=PersonStatus.ACTIVE,
        **person_data
    )
    
    session.add(person)
    await session.flush()
    
    # Log change
    await log_change(
        "person", person.id, "CREATE", current_user.id,
        old_values=None, new_values=person_data, session=session
    )
    
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
    current_user: Optional[Person] = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a person by their ID.
    
    Admin: Can view any person.
    Supervisor: Can view own profile and workers under them.
    Worker: Can view own profile only.
    """
    if not validate_person_id(person_id):
        raise HTTPException(status_code=400, detail="Invalid person ID format")
    
    # Load person with role relationship
    stmt = select(Person).options(selectinload(Person.role)).where(Person.id == person_id)
    result = await session.execute(stmt)
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # RBAC check
    if current_user:
        role_name = await get_user_role(current_user, session)
        
        if role_name == "worker":
            # Worker can only view own profile
            if person.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Workers can only view their own profile"
                )
        elif role_name == "supervisor":
            # Supervisor can view own profile and workers under them
            if person.id != current_user.id and person.supervisor_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Supervisors can only view their own profile and workers under them"
                )
        # Admin can view anyone
    
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
    current_user: Person = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a person's information.
    
    Admin: Can update all fields.
    Supervisor: Can update workers (non-monetary fields only).
    Worker: Cannot update (read-only).
    """
    if not validate_person_id(person_id):
        raise HTTPException(status_code=400, detail="Invalid person ID format")
    
    stmt = select(Person).where(Person.id == person_id)
    result = await session.execute(stmt)
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Get user role
    role_name = await get_user_role(current_user, session)
    
    # RBAC checks
    if role_name == "worker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workers cannot update their profile"
        )
    elif role_name == "supervisor":
        # Supervisor can only update workers under them
        if person.id != current_user.id and person.supervisor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors can only update workers under them"
            )
        # Filter admin-only fields
        update_data = data.model_dump(exclude_unset=True)
        update_data = filter_admin_only_fields(
            update_data, PERSON_ADMIN_ONLY_FIELDS, role_name
        )
    else:
        # Admin can update all fields
        update_data = data.model_dump(exclude_unset=True)
    
    # Store old values for audit
    old_values = {k: getattr(person, k) for k in update_data.keys() if hasattr(person, k)}
    
    # Handle password update
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))
    
    # Convert string enums to enum values
    if "employment_status" in update_data:
        update_data["employment_status"] = EmploymentStatus(update_data["employment_status"])
    if "worker_type" in update_data:
        update_data["worker_type"] = WorkerType(update_data["worker_type"])
    if "contract_type" in update_data:
        update_data["contract_type"] = ContractType(update_data["contract_type"])
    if "pay_cycle" in update_data:
        update_data["pay_cycle"] = PayCycle(update_data["pay_cycle"])
    if "insurance_enrollment_status" in update_data:
        update_data["insurance_enrollment_status"] = InsuranceStatus(update_data["insurance_enrollment_status"])
    if "payment_method" in update_data:
        update_data["payment_method"] = PaymentMethod(update_data["payment_method"])
    if "payment_status" in update_data:
        update_data["payment_status"] = PaymentStatus(update_data["payment_status"])
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(person, field):
            setattr(person, field, value)
    
    person.updated_at = __import__('datetime').datetime.utcnow()
    session.add(person)
    await session.flush()
    
    # Log change
    await log_change(
        "person", person.id, "UPDATE", current_user.id,
        old_values=old_values, new_values=update_data, session=session
    )
    
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
    current_user: Optional[Person] = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """
    List all persons with optional filters.
    
    Admin: Can list all persons.
    Supervisor: Can list own profile and workers under them.
    Worker: Can list own profile only.
    """
    stmt = select(Person).options(selectinload(Person.role))
    
    # RBAC filtering
    if current_user:
        role_name = await get_user_role(current_user, session)
        
        if role_name == "worker":
            # Worker can only see own profile
            stmt = stmt.where(Person.id == current_user.id)
        elif role_name == "supervisor":
            # Supervisor can see own profile and workers under them
            stmt = stmt.where(
                (Person.id == current_user.id) | (Person.supervisor_id == current_user.id)
            )
        # Admin can see all
    
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

