"""Input validation utilities."""
from fastapi import UploadFile, HTTPException, status
from ..config import settings


def validate_image_file(file: UploadFile):
    """Validate uploaded image file.
    
    Args:
        file: Uploaded file
        
    Raises:
        HTTPException: If file is invalid
    """
    # Check content type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPEG or PNG)"
        )
    
    # Check file extension
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    file_ext = None
    if file.filename:
        file_ext = "." + file.filename.split(".")[-1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension not allowed. Allowed: {', '.join(allowed_extensions)}"
        )


async def validate_image_size(file: UploadFile):
    """Validate image file size.
    
    Args:
        file: Uploaded file
        
    Raises:
        HTTPException: If file is too large
    """
    # Read file size
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    
    if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_IMAGE_SIZE_MB}MB"
        )
    
    # Reset file pointer
    await file.seek(0)
