import io
import cv2
import numpy as np
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from collections import Counter

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, status
from pydantic import BaseModel
from sqlmodel import Session, select, or_
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

from server.db import get_session
from server.app.dependencies import require_auth
from server.db.models import (
    Person, Attendance, AttendanceStatus, 
    FaceEmbedding, Assignment,
    OvertimeRequest, Role
)
from server.app.schemas.attendance import AttendanceResponse, AttendanceRead
from server.app.schemas.overtime import OvertimeRequestCreate, OvertimeRequestUpdate, OvertimeRequestRead
from server.app.services.face_recognition import FaceRecognitionService
from server.app.services.attendance_automation import reconcile_attendance
from server.config import config

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
    """Recognize a person by face embedding similarity."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        embedding = face_service.generate_embedding(image)
    
        # Query top 5 nearest face embeddings with cosine distance
        distance_col = FaceEmbedding.embedding.cosine_distance(embedding).label("distance")
        results = session.exec(
            select(FaceEmbedding, distance_col)
            .order_by(distance_col)
            .limit(5)
        ).all()

        if not results:
            logger.info("No face embeddings in database to match against")
            return None, None, 0.0

        # Log top results for debugging
        for i, (emb, dist) in enumerate(results):
            sim = 1 - float(dist)
            logger.info(f"  Match #{i+1}: person_id={emb.person_id}, similarity={sim:.4f}")

        # Use the best match (lowest distance / highest similarity)
        best_emb, best_dist = results[0]
        similarity = 1 - float(best_dist)

        logger.info(f"Best match: person_id={best_emb.person_id}, similarity={similarity:.4f}, threshold={config.SIMILARITY_THRESHOLD}")

        if similarity >= config.SIMILARITY_THRESHOLD and best_emb.person_id:
            person = session.get(Person, best_emb.person_id)
            if person:
                logger.info(f"✅ Recognized: {person.full_name} (ID: {person.id})")
                return person.full_name, best_emb.person_id, similarity

        logger.info(f"❌ No match above threshold ({config.SIMILARITY_THRESHOLD})")
        return None, None, similarity
    
    except ValueError as e:
        logger.warning(f"Face recognition ValueError (possible spoof): {e}")
        return None, None, 0.0

    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify", response_model=dict)
async def verify_attendance(
    file: UploadFile = File(..., description="Face image for verification"),
    site_id: Optional[UUID] = Form(None),
    shift_id: Optional[UUID] = Form(None),
    session: Session = Depends(get_session),
):
    """
    Verify a person from a face image without recording attendance.
    Returns person info and current attendance status for today.
    """
    name, person_id, similarity = await recognize_person(file, site_id, shift_id, session)
    
    if not person_id:
        return {
            "match_found": False,
            "is_real": True,
            "message": "Face recognition failed"
        }
    
    # Check current status
    attendance = get_today_attendance(session, person_id)
    status = "none"
    if attendance:
        if attendance.check_out:
            status = "checked-out"
        elif attendance.check_in:
            status = "checked-in"

    return {
        "match_found": True,
        "person_id": person_id,
        "full_name": name,
        "similarity_score": similarity,
        "current_status": status,
        "is_real": True
    }


@router.post("/check-in", response_model=AttendanceResponse)
async def check_in(
    file: UploadFile = File(..., description="Face image for verification"),
    site_id: Optional[UUID] = Form(None),
    shift_id: Optional[UUID] = Form(None),
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
        # Resolve site_id and shift_id if not provided
        today = date.today()
        if not site_id or not shift_id:
            # Look for an active assignment
            stmt = select(Assignment).where(
                Assignment.person_id == person_id,
                Assignment.effective_from <= today,
                (Assignment.effective_to == None) | (Assignment.effective_to >= today)
            ).order_by(Assignment.effective_from.desc())
            
            assignment = session.exec(stmt).first()
            
            if not assignment:
                if not site_id or not shift_id:
                    raise HTTPException(
                        status_code=400, 
                        detail="No active assignment found for person and no site/shift info provided."
                    )
        else:
            # Find matching assignment for specific site/shift
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
            # Create a temporary/adhoc assignment if we have the IDs
            if site_id and shift_id:
                assignment = Assignment(
                    person_id=person_id,
                    site_id=site_id,
                    shift_id=shift_id,
                    effective_from=today
                )
                session.add(assignment)
                session.flush()
            else:
                 raise HTTPException(
                    status_code=400, 
                    detail="Cannot create attendance: missing site/shift information and no existing assignment found."
                )

        # Create new attendance record
        attendance = Attendance(
            person_id=person_id,
            date=today,
            check_in=now,
            assignment_id=assignment.id,
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
    site_id: Optional[UUID] = Form(None),
    shift_id: Optional[UUID] = Form(None),
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
    
    # Verify attendance exists if provided, or find it by date
    attendance = None
    if request.attendance_id:
        attendance = session.get(Attendance, request.attendance_id)
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
    else:
        # Try to find attendance by date
        stmt = select(Attendance).where(
            Attendance.person_id == request.person_id,
            Attendance.date == request.overtime_date
        )
        attendance = session.exec(stmt).first()
        if not attendance:
            raise HTTPException(
                status_code=404, 
                detail="No attendance record found for this date. Cannot request overtime without an attendance record."
            )

    ot_request = OvertimeRequest(
        person_id=request.person_id,
        attendance_id=attendance.id,
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
        id=ot_request.attendance_id,
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


class ReconcileRequest(BaseModel):
    target_date: Optional[date] = None


@router.post("/reconcile")
async def reconcile_attendance_endpoint(
    request: Optional[ReconcileRequest] = None,
    current_user: Person = Depends(require_auth),
    session: Session = Depends(get_session),
):
    """
    Reconcile attendance for a target date (defaults to today).
    Admin only.
    Marks absent workers, handles missed check-outs, creates overtime requests.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can reconcile attendance")
    
    reconcile_date = (request.target_date if request else None) or date.today()
    result = reconcile_attendance(reconcile_date, session)
    
    return {
        "message": f"Attendance reconciled for {reconcile_date}",
        "target_date": reconcile_date.isoformat(),
        "absent_marked": result.get("absent_marked", 0),
        "overtime_requests_created": result.get("overtime_requests_created", 0),
    }