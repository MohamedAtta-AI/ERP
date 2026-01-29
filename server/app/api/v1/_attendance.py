import io
import cv2
import numpy as np
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from collections import Counter

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, status
from pydantic import BaseModel
from sqlmodel import Session, select
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

from server.db import get_session
from server.app.dependencies import require_auth, get_user_role
from server.db.models import (
    Person, PersonStatus, Attendance, AttendanceStatus, 
    FaceEmbedding, Assignment, SkillValue, PersonSkillLink,
    OvertimeRequest, Role
)
from server.app.schemas.attendance import AttendanceRequest, AttendanceResponse, AttendanceRead
from server.app.schemas.overtime import OvertimeRequestCreate, OvertimeRequestUpdate, OvertimeRequestRead
from server.app.services.face_recognition import FaceRecognitionService
from server.app.services.attendance_automation import reconcile_attendance
from server.config import config
from sqlalchemy import func, or_

router = APIRouter()

# Initialize face recognition service
face_service = FaceRecognitionService()


def get_today_attendance(session: Session, person_id: str) -> Optional[Attendance]:
    """Helper to find today's attendance record for a person."""
    return session.exec(
        select(Attendance).where(
            Attendance.person_id == person_id,
            Attendance.date == date.today()
        )
    ).first()


async def recognize_person(
    image: UploadFile,
    site_id: UUID,
    shift_id: UUID,
    session: Session,
):
    # Generate embedding and check anti-spoofing
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        embedding = face_service.generate_embedding(image)
    
        # Query top 3 nearest face embeddings with cosine distance
        distance_col = FaceEmbedding.embedding.cosine_distance(embedding).label("distance")
        results = session.exec(
            select(FaceEmbedding, distance_col)
            .order_by(distance_col)
            .limit(3)
        ).all()

        # Group distances by person_id
        person_matches = {} # person_id -> list of similarities
        for face_emb, dist in results:
            if face_emb.person_id:
                similarity = 1 - float(dist)
                if face_emb.person_id not in person_matches:
                    person_matches[face_emb.person_id] = []
                person_matches[face_emb.person_id].append(similarity)

        matched_person_name = None
        matched_person_id = None
        avg_similarity = 0.0

        # Check for at least two matches for any person
        for pid, similarities in person_matches.items():
            if len(similarities) >= 2:
                avg_similarity = sum(similarities) / len(similarities)
                
                # Check against threshold
                if avg_similarity < config.SIMILARITY_THRESHOLD:
                    break
                    
                matched_person_id = pid
                # Fetch person to get name
                person = session.get(Person, matched_person_id)
                if person:
                    matched_person_name = person.full_name
                break

        return matched_person_name, matched_person_id, avg_similarity
    
    except ValueError as e: # Spoofing detected
        # raise HTTPException(status_code=400, detail="Spoof detected in the given image.")
        return None, None, 0.0

    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check-in", response_model=AttendanceResponse)
async def check_in(
    file: UploadFile = File(..., description="Face image for verification"),
    site_id: UUID = Form(...),
    shift_id: UUID = Form(...),
    session: Session = Depends(get_session),
):
    # 1. Recognize person from face
    name, person_id, similarity = await recognize_person(file, site_id, shift_id, session)
    if not person_id:
        raise HTTPException(status_code=401, detail="Face recognition failed")
    
    # 2. Get/Create today's attendance
    attendance = get_today_attendance(session, person_id)
    now = datetime.utcnow()
    
    if attendance:
        if attendance.check_in:
            # Already checked in
            return AttendanceResponse(
                attendance_id=attendance.id,
                person_id=person_id,
                full_name=name,
                timestamp=attendance.check_in,
                similarity=similarity
            )

    else:
        # Find matching assignment
        today = date.today()
        assignment = session.exec(
            select(Assignment).where(
                Assignment.person_id == person_id,
                Assignment.site_id == site_id,
                Assignment.shift_id == shift_id,
                Assignment.effective_from <= today,
                (Assignment.effective_to == None) | (Assignment.effective_to >= today)
            )
        ).first()

        if not assignment:
            assignment = Assignment(
                person_id=person_id,
                site_id=site_id,
                shift_id=shift_id,
                effective_from=today
            )
            session.add(assignment)
            session.flush()

        # Create new attendance record
        # Calculate rate snapshot: assignment rate + person's skills valued at site
        skill_boost = session.exec(
            select(func.sum(SkillValue.amount))
            .join(PersonSkillLink, SkillValue.skill_id == PersonSkillLink.skill_id)
            .where(
                SkillValue.site_id == site_id,
                PersonSkillLink.person_id == person_id
            )
        ).one() or 0.0

        attendance = Attendance(
            person_id=person_id,
            date=today,
            check_in=now,
            assignment_id=assignment.id,
            rate_snapshot=assignment.rate + skill_boost
        )
        session.add(attendance)
    
    session.commit()
    session.refresh(attendance)
    
    return AttendanceResponse(
        attendance_id=attendance.id,
        person_id=person_id,
        full_name=name or "Unknown",
        timestamp=now,
        similarity=similarity
    )


@router.post("/check-out", response_model=AttendanceResponse)
async def check_out(
    file: UploadFile = File(..., description="Face image for verification"),
    site_id: UUID = Form(...),
    shift_id: UUID = Form(...),
    session: Session = Depends(get_session),
):
    # 1. Recognize person from face
    name, person_id, similarity = await recognize_person(file, site_id, shift_id, session)
    if not person_id:
        raise HTTPException(status_code=401, detail="Face recognition failed")
    
    # 2. Verify today's check-in
    attendance = get_today_attendance(session, person_id)
    
    if not attendance or not attendance.check_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No check-in found for today. Please check in first.",
        )
    
    if attendance.check_out:
        return AttendanceResponse(
            attendance_id=attendance.id,
            person_id=person_id,
            full_name=name,
            timestamp=attendance.check_out,
            similarity=similarity
        )
    
    now = datetime.utcnow()
    attendance.check_out = now
    
    session.add(attendance)
    session.commit()
    session.refresh(attendance)
    
    return AttendanceResponse(
        attendance_id=attendance.id,
        person_id=person_id,
        full_name=name,
        timestamp=now,
        similarity=similarity
    )


@router.get("/history", response_model=list[AttendanceRead])
async def get_attendance_history(
    person_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    current_user: Person = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Get attendance history with optional filters.
    Supervisor: Can see own attendance + workers under them.
    Worker: Can see own attendance only.
    Admin: Can see all attendance.
    """
    stmt = select(Attendance)
    
    # RBAC filtering: Workers are not system users, so current_user is either Supervisor or Admin
    if current_user.role == Role.SUPERVISOR:
        if person_id and person_id != current_user.id:
            # Verify person is under supervisor
            person = session.get(Person, person_id)
            if not person or person.supervisor_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Supervisors can only view attendance for themselves or workers under them"
                )
        else:
            # Filter to own + workers
            stmt = stmt.join(Person, Attendance.person_id == Person.id).where(
                or_(
                    Attendance.person_id == current_user.id,
                    Person.supervisor_id == current_user.id
                )
            )
    
    # Manual filters
    if person_id:
        stmt = stmt.where(Attendance.person_id == person_id)
    if start_date:
        stmt = stmt.where(Attendance.date >= start_date)
    if end_date:
        stmt = stmt.where(Attendance.date <= end_date)
    
    stmt = stmt.order_by(Attendance.date.desc()).limit(limit)
    attendances = session.exec(stmt).all()
    
    return [
        AttendanceRead(
            id=a.id,
            person_id=a.person_id,
            person_name=a.person.full_name if a.person else "Unknown",
            attendance_date=a.date,
            check_in=a.check_in,
            check_out=a.check_out,
            status=a.status.value if isinstance(a.status, AttendanceStatus) else a.status,
            location_name=a.assignment.site.name if a.assignment and a.assignment.site else None,
            shift_name=a.assignment.shift.name if a.assignment and a.assignment.shift else None,
        )
        for a in attendances
    ]


@router.post("/overtime", response_model=OvertimeRequestRead)
async def submit_overtime_request(
    request: OvertimeRequestCreate,
    current_user: Person = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Submit an overtime request.
    Supervisor: For themselves or workers under them.
    Admin: For anyone.
    """
    # RBAC Check: Supervisors can submit for self or their workers. Admins for anyone.
    if current_user.role == Role.SUPERVISOR:
        if request.person_id != current_user.id:
            person = session.get(Person, request.person_id)
            if not person or person.supervisor_id != current_user.id:
                raise HTTPException(status_code=403, detail="Supervisors can only submit OT for themselves or their workers")
    # Workers are not system users, so they won't be 'current_user' here.
    
    # Verify attendance exists if provided
    if request.attendance_id:
        attendance = session.get(Attendance, request.attendance_id)
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")

    ot_request = OvertimeRequest(
        person_id=request.person_id,
        attendance_id=request.attendance_id,
        hours=request.hours,
        notes=request.notes,
        status=AttendanceStatus.OVERTIME_PENDING
    )
    
    session.add(ot_request)
    session.commit()
    session.refresh(ot_request)
    
    # Note: Returning ot_request assumes it has the fields required by OvertimeRequestRead.
    # We may need to manually construct the Read object if database fields differ significantly.
    return OvertimeRequestRead(
        id=ot_request.id if hasattr(ot_request, "id") else attendance_id, # Fallback if UUID pk
        person_id=ot_request.person_id,
        person_name=session.get(Person, ot_request.person_id).full_name,
        attendance_id=ot_request.attendance_id,
        overtime_date=request.overtime_date,
        hours=ot_request.hours,
        status=ot_request.status,
        notes=ot_request.notes,
        created_at=datetime.utcnow()
    )


@router.patch("/overtime/{attendance_id}", response_model=OvertimeRequestRead)
async def manage_overtime_request(
    attendance_id: UUID,
    update: OvertimeRequestUpdate,
    current_user: Person = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Approve or deny an overtime request.
    Admin only.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can approve/deny overtime")
    
    ot_request = session.get(OvertimeRequest, attendance_id)
    if not ot_request:
        raise HTTPException(status_code=404, detail="Overtime request not found")
    
    attendance = session.get(Attendance, attendance_id)
    
    if update.status == "approved":
        ot_request.status = AttendanceStatus.OVERTIME_APPROVED
        if attendance:
            attendance.status = AttendanceStatus.OVERTIME_APPROVED
    else:
        ot_request.status = AttendanceStatus.OVERTIME_REJECTED
        if attendance:
            attendance.status = AttendanceStatus.OVERTIME_REJECTED
            
    if update.rejection_reason:
        ot_request.notes = f"{ot_request.notes or ''} [Reason: {update.rejection_reason}]"
    
    session.add(ot_request)
    if attendance:
        session.add(attendance)
        
    session.commit()
    session.refresh(ot_request)
    
    return OvertimeRequestRead(
        id=attendance_id,
        person_id=ot_request.person_id,
        person_name=session.get(Person, ot_request.person_id).full_name,
        attendance_id=ot_request.attendance_id,
        overtime_date=attendance.date if attendance else date.today(),
        hours=ot_request.hours,
        status=ot_request.status,
        notes=ot_request.notes,
        created_at=datetime.utcnow() # Simplified for read schema
    )