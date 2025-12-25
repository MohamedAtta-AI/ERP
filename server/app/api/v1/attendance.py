"""Attendance endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from typing import Optional, List

from ...database import get_db
from ...models.employee import Employee
from ...models.attendance import Attendance
from ...models.face_embedding import FaceEmbedding
from ...schemas.attendance import AttendanceCheckIn, AttendanceCheckOut, AttendanceResponse, AttendanceHistoryResponse
from ...schemas.face import FaceVerifyResponse
from ...services.face_recognition import FaceRecognitionService
from ...services.vector_search import VectorSearchService
from ...services.image_processing import process_face_crop_for_recognition
from ...utils.validators import validate_image_file, validate_image_size
from ...config import settings
from pgvector.sqlalchemy import Vector
import numpy as np

router = APIRouter(prefix="/attendance", tags=["attendance"])

# Lazy-loaded services
_face_service = None
_vector_service = None

def get_face_service():
    """Get or create face recognition service instance."""
    global _face_service
    if _face_service is None:
        _face_service = FaceRecognitionService()  # FaceNet512 via DeepFace
    return _face_service

def get_vector_service():
    """Get or create vector search service instance."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorSearchService()
    return _vector_service


@router.post("/verify", response_model=FaceVerifyResponse)
async def verify_attendance(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Verify face and return employee information."""
    print(f"[VERIFY] Received verification request")
    
    # Validate image
    validate_image_file(file)
    await validate_image_size(file)
    
    # Read image data (should be pre-cropped 160x160 face from frontend for FaceNet512)
    image_data = await file.read()
    print(f"[VERIFY] Received face crop, size: {len(image_data)} bytes")
    
    # Process pre-cropped face (validates and converts format)
    processed_image = process_face_crop_for_recognition(image_data)
    print(f"[VERIFY] Processed face crop shape: {processed_image.shape}")

    # Generate embedding with anti-spoofing check (FaceNet512 built-in)
    face_service = get_face_service()
    try:
        query_embedding, anti_spoof_result = face_service.generate_embedding(
            processed_image, 
            check_anti_spoof=True
        )
        
        # Anti-spoofing is already checked in generate_embedding() - if it fails, an exception is raised
        # If we get here, anti-spoofing passed
        if anti_spoof_result:
            print(
                f"[VERIFY] Anti-spoof passed: score={anti_spoof_result.get('antispoof_score', 1.0):.3f}"
            )
        
        print(f"[VERIFY] Generated embedding shape: {query_embedding.shape}")
    except ValueError as e:
        # Handle anti-spoofing failures and other validation errors
        error_msg = str(e)
        if "anti-spoofing failed" in error_msg.lower() or "spoof" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Liveness check failed (possible spoof). Please retry.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[VERIFY] Error during face recognition/anti-spoofing: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Face recognition service error: {str(e)}",
        )
    
    # Check how many embeddings exist in database
    count_result = await db.execute(select(FaceEmbedding))
    embeddings = count_result.scalars().all()
    print(f"[VERIFY] Total embeddings in database: {len(embeddings)}")
    
    # Search for matching face
    vector_service = get_vector_service()
    match = await vector_service.find_similar_face(
        db, query_embedding, threshold=settings.FACE_SIMILARITY_THRESHOLD
    )
    
    print(f"[VERIFY] Match result: {match}")
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Face not recognized"
        )
    
    # Get employee details
    result = await db.execute(
        select(Employee).where(Employee.id == match["employee_id"])
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return FaceVerifyResponse(
        employee_id=employee.employee_id,
        full_name=employee.full_name,
        email=employee.email,
        department=employee.department,
        similarity_score=match["similarity"],
        match_found=True
    )


@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def check_in(
    check_in_data: AttendanceCheckIn,
    db: AsyncSession = Depends(get_db)
):
    """Record employee check-in."""
    # Get employee
    result = await db.execute(
        select(Employee).where(Employee.employee_id == check_in_data.employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {check_in_data.employee_id} not found"
        )
    
    # Create attendance record
    attendance = Attendance(
        employee_id=employee.id,
        check_in_time=datetime.now(),
        location=check_in_data.location,
    )
    
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    
    return attendance


@router.post("/check-out", response_model=AttendanceResponse)
async def check_out(
    check_out_data: AttendanceCheckOut,
    db: AsyncSession = Depends(get_db)
):
    """Record employee check-out."""
    # Get employee
    result = await db.execute(
        select(Employee).where(Employee.employee_id == check_out_data.employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {check_out_data.employee_id} not found"
        )
    
    # Find today's check-in without check-out
    result = await db.execute(
        select(Attendance)
        .where(Attendance.employee_id == employee.id)
        .where(Attendance.check_out_time.is_(None))
        .order_by(desc(Attendance.check_in_time))
        .limit(1)
    )
    attendance = result.scalar_one_or_none()
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active check-in found"
        )
    
    # Update check-out time
    attendance.check_out_time = datetime.now()
    await db.commit()
    await db.refresh(attendance)
    
    return attendance


@router.get("/history", response_model=List[AttendanceHistoryResponse])
async def get_attendance_history(
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get attendance history."""
    query = select(
        Attendance,
        Employee.full_name,
        Employee.employee_id
    ).join(Employee, Attendance.employee_id == Employee.id)
    
    if employee_id:
        query = query.where(Employee.employee_id == employee_id)
    
    query = query.order_by(desc(Attendance.check_in_time)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        AttendanceHistoryResponse(
            id=attendance.id,
            employee_id=attendance.employee_id,
            employee_name=full_name,
            employee_code=emp_id,
            check_in_time=attendance.check_in_time,
            check_out_time=attendance.check_out_time,
            location=attendance.location,
            created_at=attendance.created_at
        )
        for attendance, full_name, emp_id in rows
    ]
