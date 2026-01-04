"""Employee registration endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional, List
import base64
from pathlib import Path

from ...database import get_db
from ...models.employee import Employee, EmployeeCreate, EmployeeResponse
from ...models.face_embedding import FaceEmbedding
from ...schemas.employee import FaceEnrollmentRequest, FaceEnrollmentResponse
from ...utils.employee_id_generator import get_unique_employee_id
from ...services.face_recognition import FaceRecognitionService
from ...services.image_processing import process_face_crop_for_recognition
from ...utils.validators import validate_image_file, validate_image_size
from ...settings import settings

router = APIRouter(prefix="/employees", tags=["employees"])

# Lazy-loaded face recognition service
_face_service = None


def get_face_service():
    """Get or create face recognition service instance."""
    global _face_service
    if _face_service is None:
        _face_service = FaceRecognitionService()
    return _face_service


@router.post(
    "/register", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED
)
async def register_employee(
    employee_data: EmployeeCreate, db: AsyncSession = Depends(get_db)
):
    """Register a new employee with auto-generated 6-character ID."""
    # Check if email already exists
    result = await db.exec(
        select(Employee).where(Employee.email == employee_data.email)
    )
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
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
    employee_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """Upload face image and generate embedding for employee."""
    print(f"[ENROLL] Enrolling face for employee: {employee_id}")

    # Get employee
    result = await db.exec(select(Employee).where(Employee.employee_id == employee_id))
    employee = result.first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found",
        )

    print(f"[ENROLL] Found employee: {employee.full_name} (DB ID: {employee.id})")

    # Validate image
    validate_image_file(file)
    await validate_image_size(file)

    # Read image data (should be pre-cropped 160x160 face from frontend)
    image_data = await file.read()
    print(f"[ENROLL] Received face crop, size: {len(image_data)} bytes")

    # Process pre-cropped face (validates and converts format)
    processed_image = process_face_crop_for_recognition(image_data)
    print(f"[ENROLL] Processed face crop shape: {processed_image.shape}")

    # Generate embedding with anti-spoofing check
    face_service = get_face_service()
    try:
        embedding, is_real = face_service.generate_embedding(processed_image)

        # Check anti-spoofing result
        if is_real is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Liveness check failed (possible spoof). Please retry with a live face.",
            )

        if is_real is True:
            print(f"[ENROLL] Anti-spoof passed: face is real")

        print(
            f"[ENROLL] Generated embedding shape: {embedding.shape}, first 5 values: {embedding[:5]}"
        )
    except HTTPException:
        raise
    except ValueError as e:
        error_msg = str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    except Exception as e:
        print(f"[ENROLL] Error during face recognition/anti-spoofing: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Face recognition service error: {str(e)}",
        )

    # Save image to storage
    storage_path = settings.registrations_path
    storage_path.mkdir(parents=True, exist_ok=True)
    image_filename = f"{employee_id}_{employee.id}.jpg"
    image_path = storage_path / image_filename

    with open(image_path, "wb") as f:
        f.write(image_data)
    print(f"[ENROLL] Saved image to: {image_path}")

    # Check existing embeddings count (limit to 10 per employee)
    existing_result = await db.exec(
        select(FaceEmbedding).where(FaceEmbedding.employee_id == employee.id)
    )
    existing_embeddings = existing_result.all()
    embedding_count = len(existing_embeddings)

    if embedding_count >= settings.MAX_EMBEDDINGS_PER_EMPLOYEE:
        # Remove oldest embedding
        oldest_result = await db.exec(
            select(FaceEmbedding)
            .where(FaceEmbedding.employee_id == employee.id)
            .order_by(FaceEmbedding.created_at)
            .limit(1)
        )
        oldest_embedding = oldest_result.first()
        if oldest_embedding:
            await db.delete(oldest_embedding)
            await db.commit()
            print(f"[ENROLL] Removed oldest embedding (limit reached)")
            embedding_count -= 1

    # Store new embedding
    face_embedding = FaceEmbedding(
        employee_id=employee.id,
        embedding=embedding.tolist(),  # Convert numpy array to list
        image_path=str(image_path),
    )

    db.add(face_embedding)
    await db.commit()
    await db.refresh(face_embedding)
    print(
        f"[ENROLL] Stored embedding with ID: {face_embedding.id} (Total: {embedding_count + 1})"
    )

    return {
        "message": "Face enrolled successfully",
        "employee_id": employee_id,
        "image_path": str(image_path),
        "embedding_count": embedding_count + 1,
    }


@router.post(
    "/{employee_id}/enroll-faces",
    response_model=FaceEnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_faces(
    employee_id: str, request: FaceEnrollmentRequest, db: AsyncSession = Depends(get_db)
):
    """Upload multiple face images and generate embeddings for employee (all in one request)."""
    base64_images = request.images
    if not base64_images or len(base64_images) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image is required",
        )

    print(
        f"[ENROLL] Enrolling {len(base64_images)} face angles for employee: {employee_id}"
    )

    # Get employee
    result = await db.exec(select(Employee).where(Employee.employee_id == employee_id))
    employee = result.first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found",
        )

    print(f"[ENROLL] Found employee: {employee.full_name} (DB ID: {employee.id})")

    # Get existing embeddings count
    existing_result = await db.exec(
        select(FaceEmbedding).where(FaceEmbedding.employee_id == employee.id)
    )
    existing_embeddings = existing_result.all()
    embedding_count = len(existing_embeddings)

    face_service = get_face_service()
    storage_path = settings.registrations_path
    storage_path.mkdir(parents=True, exist_ok=True)

    enrolled_count = 0
    errors = []

    # Process each image
    for idx, base64_image in enumerate(base64_images):
        try:
            # Decode base64 image
            try:
                image_data = base64.b64decode(base64_image)
            except Exception as e:
                errors.append(f"Image {idx + 1}: Invalid base64 encoding")
                continue

            # Validate size
            file_size_mb = len(image_data) / (1024 * 1024)
            if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
                errors.append(
                    f"Image {idx + 1}: File size exceeds maximum allowed size of {settings.MAX_IMAGE_SIZE_MB}MB"
                )
                continue

            # Process pre-cropped face
            try:
                processed_image = process_face_crop_for_recognition(image_data)
                print(
                    f"[ENROLL] Processed face crop {idx + 1}, shape: {processed_image.shape}"
                )
            except Exception as e:
                errors.append(f"Image {idx + 1}: Invalid face crop - {str(e)}")
                continue

            # Generate embedding with anti-spoofing check
            try:
                embedding, is_real = face_service.generate_embedding(processed_image)

                # Check anti-spoofing result
                if is_real is False:
                    errors.append(
                        f"Image {idx + 1}: Liveness check failed (possible spoof)"
                    )
                    continue

                if is_real is True:
                    print(f"[ENROLL] Image {idx + 1} - Anti-spoof passed: face is real")

                print(
                    f"[ENROLL] Generated embedding {idx + 1}, shape: {embedding.shape}"
                )
            except Exception as e:
                print(
                    f"[ENROLL] Error during face recognition for image {idx + 1}: {e}"
                )
                errors.append(f"Image {idx + 1}: Face recognition error - {str(e)}")
                continue

            # Save image to storage
            image_filename = f"{employee_id}_{employee.id}_{idx + 1}.jpg"
            image_path = storage_path / image_filename

            with open(image_path, "wb") as f:
                f.write(image_data)
            print(f"[ENROLL] Saved image {idx + 1} to: {image_path}")

            # Check if we need to remove oldest embeddings (limit to 10 per employee)
            if embedding_count + enrolled_count >= settings.MAX_EMBEDDINGS_PER_EMPLOYEE:
                # Remove oldest embedding
                oldest_result = await db.exec(
                    select(FaceEmbedding)
                    .where(FaceEmbedding.employee_id == employee.id)
                    .order_by(FaceEmbedding.created_at)
                    .limit(1)
                )
                oldest_embedding = oldest_result.first()
                if oldest_embedding:
                    await db.delete(oldest_embedding)
                    await db.commit()
                    print(f"[ENROLL] Removed oldest embedding (limit reached)")
                    embedding_count -= 1

            # Store new embedding
            face_embedding = FaceEmbedding(
                employee_id=employee.id,
                embedding=embedding.tolist(),
                image_path=str(image_path),
            )

            db.add(face_embedding)
            enrolled_count += 1

        except Exception as e:
            print(f"[ENROLL] Error processing image {idx + 1}: {e}")
            errors.append(f"Image {idx + 1}: {str(e)}")
            continue

    # Commit all embeddings at once
    if enrolled_count > 0:
        await db.commit()
        print(
            f"[ENROLL] Stored {enrolled_count} embeddings (Total: {embedding_count + enrolled_count})"
        )

    # If there were errors but some succeeded, include them in response
    if errors and enrolled_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to enroll faces: {'; '.join(errors)}",
        )

    response_message = f"Enrolled {enrolled_count} face angle(s) successfully"
    if errors:
        response_message += f" ({len(errors)} failed: {'; '.join(errors)})"

    return {
        "message": response_message,
        "employee_id": employee_id,
        "enrolled_count": enrolled_count,
        "embedding_count": embedding_count + enrolled_count,
    }


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: str, db: AsyncSession = Depends(get_db)):
    """Get employee details by employee ID."""
    result = await db.exec(select(Employee).where(Employee.employee_id == employee_id))
    employee = result.first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found",
        )

    return employee
