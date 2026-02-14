import cv2
import numpy as np
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, status
from pydantic import BaseModel, Field
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


def _resolve_assignment(
    session: Session,
    person_id: str,
    target_date: date,
    site_id: Optional[UUID],
    shift_id: Optional[UUID],
) -> Optional[Assignment]:
    if site_id and shift_id:
        return session.exec(
            select(Assignment).where(
                Assignment.person_id == person_id,
                Assignment.site_id == site_id,
                Assignment.shift_id == shift_id,
                Assignment.effective_from <= target_date,
                (Assignment.effective_to == None) | (Assignment.effective_to >= target_date),
            ).order_by(Assignment.effective_from.desc())
        ).first()

    return session.exec(
        select(Assignment).where(
            Assignment.person_id == person_id,
            Assignment.effective_from <= target_date,
            (Assignment.effective_to == None) | (Assignment.effective_to >= target_date),
        ).order_by(Assignment.effective_from.desc())
    ).first()


def _get_open_attendance(
    session: Session,
    person_id: str,
    target_date: date,
    site_id: Optional[UUID] = None,
    shift_id: Optional[UUID] = None,
) -> Optional[Attendance]:
    stmt = (
        select(Attendance)
        .join(Assignment, Attendance.assignment_id == Assignment.id, isouter=True)
        .where(
            Attendance.person_id == person_id,
            Attendance.date == target_date,
            Attendance.check_out == None,
        )
    )
    if site_id:
        stmt = stmt.where(Assignment.site_id == site_id)
    if shift_id:
        stmt = stmt.where(Assignment.shift_id == shift_id)
    stmt = stmt.order_by(Attendance.check_in.desc())
    return session.exec(stmt).first()


def _get_latest_attendance(
    session: Session,
    person_id: str,
    target_date: date,
    site_id: Optional[UUID] = None,
    shift_id: Optional[UUID] = None,
) -> Optional[Attendance]:
    stmt = (
        select(Attendance)
        .join(Assignment, Attendance.assignment_id == Assignment.id, isouter=True)
        .where(
            Attendance.person_id == person_id,
            Attendance.date == target_date,
        )
    )
    if site_id:
        stmt = stmt.where(Assignment.site_id == site_id)
    if shift_id:
        stmt = stmt.where(Assignment.shift_id == shift_id)
    stmt = stmt.order_by(Attendance.check_in.desc())
    return session.exec(stmt).first()


def _attendance_state(attendance: Attendance) -> str:
    if attendance.overtime_request:
        return attendance.overtime_request.status.value
    if attendance.check_out:
        return "checked-out"
    if attendance.check_in:
        return "checked-in"
    return "none"


def _to_overtime_read(session: Session, ot_request: OvertimeRequest) -> OvertimeRequestRead:
    person = session.get(Person, ot_request.person_id) if ot_request.person_id else None
    attendance = session.get(Attendance, ot_request.attendance_id)
    return OvertimeRequestRead(
        id=ot_request.attendance_id,
        person_id=ot_request.person_id or "",
        person_name=person.full_name if person else "Unknown",
        attendance_id=ot_request.attendance_id,
        overtime_date=attendance.date if attendance else date.today(),
        hours=ot_request.hours,
        status=ot_request.status.value if isinstance(ot_request.status, AttendanceStatus) else str(ot_request.status),
        notes=ot_request.notes,
        created_at=datetime.utcnow(),
    )


def _can_supervisor_access_person(current_user: Person, person: Person) -> bool:
    return current_user.id == person.id or person.role == Role.WORKER


class AttendanceImportRow(BaseModel):
    person_id: str = Field(..., min_length=1)
    attendance_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    site_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None


class AttendanceImportRequest(BaseModel):
    rows: List[AttendanceImportRow]
    replace_existing: bool = False


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
    
    # Check current status for specific site/shift context when provided.
    today = date.today()
    open_attendance = _get_open_attendance(session, person_id, today, site_id, shift_id)
    latest_attendance = _get_latest_attendance(session, person_id, today, site_id, shift_id)

    status = "none"
    if open_attendance:
        status = "checked-in"
    elif latest_attendance and latest_attendance.check_out:
        status = "checked-out"

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
    
    # 2. Resolve assignment and context-specific open attendance
    today = date.today()
    now = datetime.utcnow()
    existing_open = _get_open_attendance(session, person_id, today, site_id, shift_id)
    if existing_open and existing_open.check_in:
        return AttendanceResponse(
            attendance_id=existing_open.id,
            person_id=person_id,
            full_name=name,
            timestamp=existing_open.check_in,
            similarity=similarity,
        )

    assignment = _resolve_assignment(session, person_id, today, site_id, shift_id)
    if not assignment:
        if site_id and shift_id:
            assignment = Assignment(
                person_id=person_id,
                site_id=site_id,
                shift_id=shift_id,
                effective_from=today,
            )
            session.add(assignment)
            session.flush()
        else:
            raise HTTPException(
                status_code=400,
                detail="No active assignment found for person and no site/shift info provided.",
            )

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
    
    # 2. Verify open check-in in current site/shift context (if provided)
    today = date.today()
    attendance = _get_open_attendance(session, person_id, today, site_id, shift_id)
    if not attendance or not attendance.check_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active check-in found for this site/shift today. Please check in first.",
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
            # Supervisors can view workers plus themselves.
            person = session.get(Person, person_id)
            if not person or not _can_supervisor_access_person(current_user, person):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Supervisors can only view attendance for themselves or workers"
                )
        else:
            # Filter to own + all workers for consistent visibility.
            stmt = stmt.join(Person, Attendance.person_id == Person.id).where(
                or_(
                    Attendance.person_id == current_user.id,
                    Person.role == Role.WORKER
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
            status=_attendance_state(a),
            location_name=a.assignment.site.name if a.assignment and a.assignment.site else None,
            shift_name=a.assignment.shift.name if a.assignment and a.assignment.shift else None,
            assignment_title=a.assignment.title if a.assignment else None,
            assignment_rate=a.assignment.rate if a.assignment else None,
        )
        for a in attendances
    ]


@router.post("/import")
async def import_attendance(
    request: AttendanceImportRequest,
    current_user: Person = Depends(require_auth),
    session: Session = Depends(get_session),
):
    if current_user.role not in {Role.ADMIN, Role.SUPERVISOR}:
        raise HTTPException(status_code=403, detail="Only supervisors or admins can import attendance")

    created = 0
    updated = 0
    skipped = 0
    failed = 0
    errors = []

    for index, row in enumerate(request.rows):
        row_number = index + 2
        try:
            person = session.get(Person, row.person_id)
            if not person:
                raise ValueError("Person not found")

            if current_user.role == Role.SUPERVISOR and not _can_supervisor_access_person(current_user, person):
                raise ValueError("You are not allowed to import attendance for this person")

            assignment = _resolve_assignment(
                session,
                row.person_id,
                row.attendance_date,
                row.site_id,
                row.shift_id,
            )
            if not assignment and row.site_id and row.shift_id:
                assignment = Assignment(
                    person_id=row.person_id,
                    site_id=row.site_id,
                    shift_id=row.shift_id,
                    effective_from=row.attendance_date,
                )
                session.add(assignment)
                session.flush()

            if not assignment:
                raise ValueError("No assignment found for person/date. Include site_id and shift_id in import.")

            check_in_value = row.check_in or row.check_out
            if not check_in_value:
                raise ValueError("Either check_in or check_out must be provided")

            existing = session.exec(
                select(Attendance).where(
                    Attendance.person_id == row.person_id,
                    Attendance.date == row.attendance_date,
                    Attendance.assignment_id == assignment.id,
                )
            ).first()

            if existing:
                if not request.replace_existing:
                    skipped += 1
                    continue
                existing.check_in = check_in_value
                existing.check_out = row.check_out
                session.add(existing)
                updated += 1
            else:
                attendance = Attendance(
                    person_id=row.person_id,
                    date=row.attendance_date,
                    check_in=check_in_value,
                    check_out=row.check_out,
                    assignment_id=assignment.id,
                )
                session.add(attendance)
                created += 1
        except Exception as exc:
            failed += 1
            errors.append(f"Row {row_number}: {str(exc)}")

    session.commit()
    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
        "errors": errors[:10],
    }


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
            if not person or not _can_supervisor_access_person(current_user, person):
                raise HTTPException(status_code=403, detail="Supervisors can only submit OT for themselves or workers")
    elif current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only supervisors or admins can submit overtime")
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

    existing_request = session.get(OvertimeRequest, attendance.id)
    if existing_request:
        raise HTTPException(status_code=400, detail="Overtime request already exists for this attendance record")

    target_person = session.get(Person, request.person_id)
    if not target_person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Auto-approval policy:
    # - Admin-created overtime for workers or supervisors is auto-approved.
    # - Supervisor-created overtime for workers is auto-approved.
    # - Supervisor-created overtime for self remains pending for admin decision.
    initial_status = AttendanceStatus.OVERTIME_PENDING
    if current_user.role == Role.ADMIN and target_person.role in {Role.WORKER, Role.SUPERVISOR}:
        initial_status = AttendanceStatus.OVERTIME_APPROVED
    elif current_user.role == Role.SUPERVISOR and target_person.role == Role.WORKER:
        initial_status = AttendanceStatus.OVERTIME_APPROVED

    ot_request = OvertimeRequest(
        person_id=request.person_id,
        attendance_id=attendance.id,
        hours=request.hours,
        notes=request.notes,
        status=initial_status
    )
    
    session.add(ot_request)
    session.commit()
    session.refresh(ot_request)
    
    # Note: Returning ot_request assumes it has the fields required by OvertimeRequestRead.
    # We may need to manually construct the Read object if database fields differ significantly.
    return _to_overtime_read(session, ot_request)


@router.get("/overtime", response_model=list[OvertimeRequestRead])
async def list_overtime_requests(
    person_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: Person = Depends(require_auth),
    session: Session = Depends(get_session),
):
    stmt = select(OvertimeRequest)

    if current_user.role == Role.SUPERVISOR:
        worker_ids = session.exec(
            select(Person.id).where(Person.role == Role.WORKER)
        ).all()
        allowed_ids = list(set(worker_ids + [current_user.id]))
        stmt = stmt.where(OvertimeRequest.person_id.in_(allowed_ids))
    elif current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only supervisors or admins can list overtime requests")

    if person_id:
        stmt = stmt.where(OvertimeRequest.person_id == person_id)

    if status:
        normalized = status.strip().lower()
        status_map = {
            "pending": AttendanceStatus.OVERTIME_PENDING,
            "approved": AttendanceStatus.OVERTIME_APPROVED,
            "rejected": AttendanceStatus.OVERTIME_REJECTED,
            "overtime_pending": AttendanceStatus.OVERTIME_PENDING,
            "overtime_approved": AttendanceStatus.OVERTIME_APPROVED,
            "overtime_rejected": AttendanceStatus.OVERTIME_REJECTED,
        }
        if normalized in status_map:
            stmt = stmt.where(OvertimeRequest.status == status_map[normalized])

    requests = session.exec(stmt).all()
    filtered = []
    for request in requests:
        attendance = session.get(Attendance, request.attendance_id)
        if not attendance:
            continue
        if start_date and attendance.date < start_date:
            continue
        if end_date and attendance.date > end_date:
            continue
        filtered.append(request)

    return [_to_overtime_read(session, request) for request in filtered]


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
    
    if update.status == "approved":
        ot_request.status = AttendanceStatus.OVERTIME_APPROVED
    else:
        ot_request.status = AttendanceStatus.OVERTIME_REJECTED
            
    if update.rejection_reason:
        ot_request.notes = f"{ot_request.notes or ''} [Reason: {update.rejection_reason}]"
    
    session.add(ot_request)
        
    session.commit()
    session.refresh(ot_request)
    
    return _to_overtime_read(session, ot_request)


@router.delete("/overtime/{attendance_id}")
async def delete_overtime_request(
    attendance_id: UUID,
    current_user: Person = Depends(require_auth),
    session: Session = Depends(get_session),
):
    ot_request = session.get(OvertimeRequest, attendance_id)
    if not ot_request:
        raise HTTPException(status_code=404, detail="Overtime request not found")

    if current_user.role == Role.SUPERVISOR:
        if ot_request.person_id != current_user.id:
            person = session.get(Person, ot_request.person_id)
            if not person or not _can_supervisor_access_person(current_user, person):
                raise HTTPException(status_code=403, detail="Not authorized for this overtime request")
        if ot_request.status != AttendanceStatus.OVERTIME_PENDING:
            raise HTTPException(status_code=403, detail="Supervisors can only delete pending overtime requests")
    elif current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only supervisors or admins can delete overtime requests")

    session.delete(ot_request)
    session.commit()
    return {"ok": True}


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
