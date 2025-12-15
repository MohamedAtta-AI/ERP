"""Employee registration endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from ...database import get_db
from ...models.employee import Employee
from ...models.face_embedding import FaceEmbedding
from ...schemas.employee import EmployeeCreate, EmployeeResponse
from ...utils.employee_id_generator import get_unique_employee_id
from ...services.face_recognition import FaceRecognitionService
from ...services.image_processing import process_image_for_recognition
from ...utils.validators import validate_image_file, validate_image_size
from ...config import settings
import os
from pathlib import Path

router = APIRouter(prefix="/employees", tags=["employees"])

# Lazy-loaded face recognition service
_face_service = None

def get_face_service():
    """Get or create face recognition service instance."""
    global _face_service
    if _face_service is None:
        _face_service = FaceRecognitionService(settings.SFACE_MODEL_PATH)
    return _face_service


@router.post("/register", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def register_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new employee with auto-generated 5-character ID."""
    # Check if email already exists
    result = await db.execute(
        select(Employee).where(Employee.email == employee_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate unique employee ID
    employee_id = await get_unique_employee_id(db)
    
    # Create employee
    employee = Employee(
        employee_id=employee_id,
        full_name=employee_data.full_name,
        email=employee_data.email,
        department=employee_data.department,
        phone=employee_data.phone,
        position=employee_data.position,
    )
    
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    
    return employee


@router.post("/{employee_id}/enroll-face", status_code=status.HTTP_201_CREATED)
async def enroll_face(
    employee_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload face image and generate embedding for employee."""
    print(f"[ENROLL] Enrolling face for employee: {employee_id}")
    
    # Get employee
    result = await db.execute(
        select(Employee).where(Employee.employee_id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )
    
    print(f"[ENROLL] Found employee: {employee.full_name} (DB ID: {employee.id})")
    
    # Validate image
    validate_image_file(file)
    await validate_image_size(file)
    
    # Read image data
    image_data = await file.read()
    print(f"[ENROLL] Image size: {len(image_data)} bytes")
    
    # Process image
    processed_image = process_image_for_recognition(image_data)
    print(f"[ENROLL] Processed image shape: {processed_image.shape}")
    
    # Generate embedding
    face_service = get_face_service()
    embedding = face_service.generate_embedding(processed_image)
    print(f"[ENROLL] Generated embedding shape: {embedding.shape}, first 5 values: {embedding[:5]}")
    
    # Save image to storage
    storage_path = Path(settings.STORAGE_PATH) / "registrations"
    storage_path.mkdir(parents=True, exist_ok=True)
    image_filename = f"{employee_id}_{employee.id}.jpg"
    image_path = storage_path / image_filename
    
    with open(image_path, "wb") as f:
        f.write(image_data)
    print(f"[ENROLL] Saved image to: {image_path}")
    
    # Store embedding
    face_embedding = FaceEmbedding(
        employee_id=employee.id,
        embedding=embedding.tolist(),  # Convert numpy array to list
        image_path=str(image_path)
    )
    
    db.add(face_embedding)
    await db.commit()
    await db.refresh(face_embedding)
    print(f"[ENROLL] Stored embedding with ID: {face_embedding.id}")
    
    return {
        "message": "Face enrolled successfully",
        "employee_id": employee_id,
        "image_path": str(image_path)
    }


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get employee details by employee ID."""
    result = await db.execute(
        select(Employee).where(Employee.employee_id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )
    
    return employee
