from typing import List, Optional
from uuid import uuid4
from pathlib import Path
import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select

from server.db import get_session
from server.db.models import Person, PaymentInfo, Role, PersonStatus, Document, DocType
from server.app.schemas.person import (
    PersonCreate,
    PersonRead,
    PersonUpdate,
    PaymentInfoCreate,
    PaymentInfoRead,
)
from server.app.dependencies import (
    require_auth,
    require_admin,
    require_supervisor_or_admin,
)
from server.app.services.password_service import hash_password
from server.app.services.person_id_generator import generate_person_id
from server.app.services.face_recognition import FaceRecognitionService
from server.db.models import FaceEmbedding

router = APIRouter()


@router.post("/", response_model=PersonRead)
async def register_person(
    person_in: PersonCreate,
    session: Session = Depends(get_session),
    current_user: Person = Depends(require_auth),
):
    # RBAC: supervisors can only register workers
    if current_user.role == Role.SUPERVISOR and person_in.role != Role.WORKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisors can only register workers.",
        )

    # Check if user with National ID exists
    if person_in.nationalID:
        existing = session.exec(
            select(Person).where(Person.nationalID == person_in.nationalID)
        ).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="Person with this National ID already exists"
            )

    # Generate ID
    new_id = generate_person_id(lambda id: session.get(Person, id) is not None)

    # Password: use provided or default
    raw_pwd = person_in.password_hash or "ChangeMe123!"
    pwd_hash = hash_password(raw_pwd)

    # Set hire_date to today if not provided
    person_data = person_in.model_dump(exclude={"password_hash"})
    if not person_data.get("hire_date"):
        from datetime import date

        person_data["hire_date"] = date.today()

    # Only set worker_type for workers
    if person_data.get("role") != Role.WORKER:
        person_data["worker_type"] = None

    person = Person(id=new_id, **person_data, password_hash=pwd_hash)

    session.add(person)
    session.commit()
    session.refresh(person)
    return person


@router.get("/", response_model=List[PersonRead])
async def list_persons(
    role: Optional[Role] = None,
    status: Optional[PersonStatus] = None,
    limit: int = 100,
    session: Session = Depends(get_session),
    # current_user: Person = Depends(require_auth)
):
    stmt = select(Person)
    if role:
        stmt = stmt.where(Person.role == role)
    if status:
        stmt = stmt.where(Person.status == status)

    stmt = stmt.limit(limit)
    return session.exec(stmt).all()


@router.get("/check-identity")
async def check_identity(
    national_id: Optional[str] = None,
    passport: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Check if national ID or passport is already registered. Used for live form validation."""
    result = {"nationalID_taken": False, "passport_taken": False}
    if national_id and national_id.strip():
        existing = session.exec(
            select(Person).where(Person.nationalID == national_id.strip())
        ).first()
        result["nationalID_taken"] = existing is not None
    if passport and passport.strip():
        existing = session.exec(
            select(Person).where(Person.passport == passport.strip())
        ).first()
        result["passport_taken"] = existing is not None
    return result


@router.get("/{person_id}", response_model=PersonRead)
async def get_person(
    person_id: str,
    session: Session = Depends(get_session),
):
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.patch("/{person_id}", response_model=PersonRead)
async def update_person(
    person_id: str,
    person_in: PersonUpdate,
    session: Session = Depends(get_session),
    current_user: Person = Depends(require_supervisor_or_admin),
):
    """Update a person. Admins can update anyone; supervisors can only update workers."""
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if current_user.role == Role.SUPERVISOR and person.role != Role.WORKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisors can only update workers.",
        )

    update_data = person_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(person, key, value)

    session.add(person)
    session.commit()
    session.refresh(person)
    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: str,
    session: Session = Depends(get_session),
    current_user: Person = Depends(require_admin),
):
    """Soft-delete a person by setting status to TERMINATED. Admin only."""
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    person.status = PersonStatus.TERMINATED
    session.add(person)
    session.commit()


@router.post("/{person_id}/payment-info", response_model=PaymentInfoRead)
async def save_payment_info(
    person_id: str,
    info_in: PaymentInfoCreate,
    session: Session = Depends(get_session),
):
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Check if exists, update or create
    # Since model has person_id as PK, we check by that.
    existing = session.get(PaymentInfo, person_id)
    if existing:
        for k, v in info_in.model_dump().items():
            if k != "person_id":  # PK shouldn't change
                setattr(existing, k, v)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        # Create
        payment_info = PaymentInfo(**info_in.model_dump())
        # ensure person_id matches path
        payment_info.person_id = person_id
        session.add(payment_info)
        session.commit()
        session.refresh(payment_info)
        return payment_info


# Face enrollment stub?
# Already exists in attendance.py? No, attendance.py has check-in.
# I need enroll endpoint.
@router.post("/{person_id}/enroll-face")
async def enroll_face(
    person_id: str,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    service = FaceRecognitionService()

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    try:
        embedding_vector = service.generate_embedding(image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Always append a new embedding (supports multi-angle enrollment)
    face_emb = FaceEmbedding(person_id=person_id, embedding=embedding_vector)
    session.add(face_emb)
    session.commit()

    return {"message": "Face enrolled successfully"}


@router.post("/{person_id}/documents")
async def upload_document(
    person_id: str,
    file: UploadFile = File(...),
    type: str = Form(...),
    session: Session = Depends(get_session),
    current_user: Person = Depends(require_auth),
):
    """Upload a document for a person"""
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Validate document type
    try:
        doc_type = DocType(type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Must be one of: {[e.value for e in DocType]}",
        )

    # Create uploads directory if it doesn't exist
    upload_dir = Path("/app/data/uploads/documents")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_extension = Path(file.filename).suffix if file.filename else ".pdf"
    file_path = upload_dir / f"{person_id}_{doc_type.value}_{uuid4()}{file_extension}"

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # Create document record
    document = Document(person_id=person_id, type=doc_type, url=str(file_path))
    session.add(document)
    session.commit()
    session.refresh(document)

    return {
        "id": str(document.id),
        "type": doc_type.value,
        "url": str(file_path),
        "message": "Document uploaded successfully",
    }
