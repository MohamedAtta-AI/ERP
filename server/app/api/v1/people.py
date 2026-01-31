from typing import List, Optional
from uuid import UUID
import random
import string

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select

from server.db import get_session
from server.db.models import Person, PaymentInfo, Role, PersonStatus
from server.app.schemas.person import PersonCreate, PersonRead, PersonUpdate, PaymentInfoCreate, PaymentInfoRead
from server.app.dependencies import require_auth
from server.app.services.password_service import hash_password
from server.app.services.person_id_generator import generate_person_id

router = APIRouter()

@router.post("/", response_model=PersonRead)
async def register_person(
    person_in: PersonCreate,
    session: Session = Depends(get_session),
    current_user: Person = Depends(require_auth)
):
    # RBAC: supervisors can only register workers
    if current_user.role == Role.SUPERVISOR and person_in.role != Role.WORKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisors can only register workers."
        )

    # Check if user with National ID exists
    if person_in.nationalID:
        existing = session.exec(select(Person).where(Person.nationalID == person_in.nationalID)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Person with this National ID already exists")

    # Generate ID
    new_id = generate_person_id(lambda id: session.get(Person, id) is not None)
    
    # Password: use provided or default
    raw_pwd = person_in.password_hash or "ChangeMe123!"
    pwd_hash = hash_password(raw_pwd)
    
    person = Person(
        id=new_id,
        **person_in.model_dump(exclude={"password_hash"}),
        password_hash=pwd_hash
    )
    
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

@router.get("/{person_id}", response_model=PersonRead)
async def get_person(
    person_id: str,
    session: Session = Depends(get_session),
):
    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

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
            if k != "person_id": # PK shouldn't change
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
    # Just a skeleton, user didn't ask to rewrite face logic but verify routes.
    # If the client calls it, it needs to exist.
    # Client: `api.js` -> `ENROLL_FACE: ...`
    # Check `attendance.py`? It was check-in/out.
    # Where was face enrollment?
    # It was likely in the old implementation. I should add it here.
    
    from server.app.services.face_recognition import FaceRecognitionService
    from server.db.models import FaceEmbedding
    import cv2
    import numpy as np

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

    # Save
    face_emb = FaceEmbedding(person_id=person_id, embedding=embedding_vector)
    session.add(face_emb)
    session.commit()
    
    return {"message": "Face enrolled successfully"}
