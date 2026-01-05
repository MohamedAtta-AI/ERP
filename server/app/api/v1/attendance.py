"""
Attendance API endpoints.

Handles face verification and check-in/check-out recording.
"""

import io
import numpy as np
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from server.app.database import get_session
from server.app.schemas.attendance import (
    AttendanceVerifyResponse,
    AttendanceCheckInRequest,
    AttendanceCheckInResponse,
    AttendanceCheckOutRequest,
    AttendanceCheckOutResponse,
    AttendanceRead,
)
from server.db.models import Person, Attendance, AttendanceStatus, Location
from server.services.face_recognition import FaceRecognitionService
from server.app.services.attendance_automation import reconcile_attendance
from server.config import config

router = APIRouter()

# Initialize face recognition service
face_service = FaceRecognitionService()


@router.post("/verify", response_model=AttendanceVerifyResponse)
async def verify_attendance(
    file: UploadFile = File(..., description="Face image for verification"),
    location_id: Optional[UUID] = Form(None),
    shift_id: Optional[UUID] = Form(None),
    session: AsyncSession = Depends(get_session),
):
    """
    Verify a face against enrolled persons.
    
    Performs:
    1. Face detection and embedding extraction
    2. Anti-spoofing check (is_real)
    3. Vector similarity search against enrolled faces
    4. Returns match if similarity >= threshold
    """
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
    
    # Generate embedding and check anti-spoofing
    try:
        embedding, is_real = face_service.generate_embedding(image)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Anti-spoofing check - reject if spoofing detected
    if is_real is False:
        return AttendanceVerifyResponse(
            match_found=False,
            is_real=False,
            message="Spoofing detected. Please use your real face.",
        )
    
    # Query all persons with face embeddings
    stmt = select(Person).where(
        and_(
            Person.face_embedding.isnot(None),
            Person.status == "active",
        )
    )
    result = await session.execute(stmt)
    persons = result.scalars().all()
    
    if not persons:
        return AttendanceVerifyResponse(
            match_found=False,
            is_real=is_real,
            message="No enrolled faces found",
        )
    
    # Find best match using face recognition service
    candidate_embeddings = [np.array(p.face_embedding, dtype=np.float32) for p in persons]
    best_idx, best_score = face_service.find_best_match(embedding, candidate_embeddings)
    
    if best_idx is not None:
        matched_person = persons[best_idx]
        return AttendanceVerifyResponse(
            match_found=True,
            person_id=matched_person.id,
            full_name=matched_person.full_name,
            department=matched_person.department,
            similarity_score=best_score,
            is_real=is_real,
            message="Face verified successfully",
        )
    
    return AttendanceVerifyResponse(
        match_found=False,
        similarity_score=best_score if best_score > 0 else None,
        is_real=is_real,
        message="Face not recognized",
    )


@router.post("/check-in", response_model=AttendanceCheckInResponse)
async def check_in(
    request: AttendanceCheckInRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Record a check-in for a verified person.
    
    Should be called after successful face verification.
    Creates or updates attendance record for today.
    """
    person_id = request.person_id
    
    # Verify person exists
    stmt = select(Person).where(Person.id == person_id)
    result = await session.execute(stmt)
    person = result.scalar_one_or_none()
    
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    today = date.today()
    now = datetime.utcnow()
    
    # Check for existing attendance today
    stmt = select(Attendance).where(
        and_(
            Attendance.person_id == person_id,
            Attendance.attendance_date == today,
        )
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        if existing.check_in:
            # Already checked in - return existing record
            return AttendanceCheckInResponse(
                attendance_id=existing.id,
                person_id=person_id,
                full_name=person.full_name,
                check_in_time=existing.check_in,
                message="Already checked in today",
            )
        else:
            # Update existing record
            existing.check_in = now
            existing.status = AttendanceStatus.PRESENT
            existing.updated_at = now
            session.add(existing)
            attendance = existing
    else:
        # Create new attendance record
        attendance = Attendance(
            person_id=person_id,
            location_id=request.location_id,
            shift_id=request.shift_id,
            attendance_date=today,
            check_in=now,
            status=AttendanceStatus.PRESENT,
        )
        session.add(attendance)
    
    await session.flush()
    
    # Get location name if provided
    location_name = None
    if request.location_id:
        loc_result = await session.execute(
            select(Location).where(Location.id == request.location_id)
        )
        location = loc_result.scalar_one_or_none()
        if location:
            location_name = location.name
    
    return AttendanceCheckInResponse(
        attendance_id=attendance.id,
        person_id=person_id,
        full_name=person.full_name,
        check_in_time=now,
        location=location_name,
        message="Check-in recorded successfully",
    )


@router.post("/check-out", response_model=AttendanceCheckOutResponse)
async def check_out(
    request: AttendanceCheckOutRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Record a check-out for a person.
    
    Finds today's attendance record and updates check_out time.
    """
    person_id = request.person_id
    today = date.today()
    now = datetime.utcnow()
    
    # Find today's attendance
    stmt = select(Attendance).where(
        and_(
            Attendance.person_id == person_id,
            Attendance.attendance_date == today,
        )
    )
    result = await session.execute(stmt)
    attendance = result.scalar_one_or_none()
    
    if not attendance:
        raise HTTPException(
            status_code=404,
            detail="No check-in found for today. Please check in first.",
        )
    
    if not attendance.check_in:
        raise HTTPException(
            status_code=400,
            detail="Must check in before checking out",
        )
    
    # Update check-out
    attendance.check_out = now
    attendance.updated_at = now
    session.add(attendance)
    
    # Calculate total hours
    total_hours = None
    if attendance.check_in:
        delta = now - attendance.check_in
        total_hours = round(delta.total_seconds() / 3600, 2)
    
    return AttendanceCheckOutResponse(
        attendance_id=attendance.id,
        person_id=person_id,
        check_out_time=now,
        total_hours=total_hours,
        message="Check-out recorded successfully",
    )


@router.get("/history", response_model=list[AttendanceRead])
async def get_attendance_history(
    person_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """
    Get attendance history with optional filters.
    """
    stmt = select(Attendance).options(
        selectinload(Attendance.person),
        selectinload(Attendance.location),
        selectinload(Attendance.shift),
    )
    
    conditions = []
    if person_id:
        conditions.append(Attendance.person_id == person_id)
    if start_date:
        conditions.append(Attendance.attendance_date >= start_date)
    if end_date:
        conditions.append(Attendance.attendance_date <= end_date)
    
    if conditions:
        stmt = stmt.where(and_(*conditions))
    
    stmt = stmt.order_by(Attendance.attendance_date.desc()).limit(limit)
    
    result = await session.execute(stmt)
    attendances = result.scalars().all()
    
    return [
        AttendanceRead(
            id=a.id,
            person_id=a.person_id,
            person_name=a.person.full_name if a.person else "Unknown",
            attendance_date=a.attendance_date,
            check_in=a.check_in,
            check_out=a.check_out,
            status=a.status.value if isinstance(a.status, AttendanceStatus) else a.status,
            location_name=a.location.name if a.location else None,
            shift_name=a.shift.name if a.shift else None,
            similarity_score=a.similarity_score,
            is_real=a.is_real,
        )
        for a in attendances
    ]


class ReconcileRequest(BaseModel):
    target_date: Optional[date] = None


class ReconcileResponse(BaseModel):
    target_date: date
    absent_marked: int
    overtime_pending_marked: int
    overtime_requests_created: int
    message: str


@router.post("/reconcile", response_model=ReconcileResponse)
async def reconcile_attendance_endpoint(
    request: ReconcileRequest = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Reconcile attendance for a specific date (or today).
    
    This endpoint:
    1. Marks absent for employees who didn't check in
    2. Creates overtime requests for employees who checked in but not out
    
    Should be called at the end of each work day or before payroll processing.
    """
    target = request.target_date if request and request.target_date else date.today()
    
    try:
        stats = await reconcile_attendance(target, session)
        await session.commit()
        
        return ReconcileResponse(
            target_date=target,
            absent_marked=stats["absent_marked"],
            overtime_pending_marked=stats["overtime_pending_marked"],
            overtime_requests_created=stats["overtime_requests_created"],
            message=f"Reconciliation complete for {target}",
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")


