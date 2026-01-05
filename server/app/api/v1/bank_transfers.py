"""
Bank Transfer File API endpoints.

Admin only - handles bank transfer file generation and download.
"""

from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.database import get_session
from server.app.dependencies import require_role
from server.app.services.bank_transfer_service import generate_bank_file
from server.db.models import Person

router = APIRouter()


@router.post("/generate")
async def generate_bank_transfer_file(
    payroll_run_id: UUID,
    format: str = "csv",  # "csv" or "excel"
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Generate bank transfer file (Admin only)."""
    if format not in ["csv", "excel"]:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'excel'")
    
    filepath = await generate_bank_file(payroll_run_id, session, format=format)
    
    return {
        "payroll_run_id": payroll_run_id,
        "format": format,
        "file_path": str(filepath),
    }


@router.get("/{payroll_run_id}/download")
async def download_bank_transfer_file(
    payroll_run_id: UUID,
    format: str = "csv",
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Download bank transfer file."""
    filepath = await generate_bank_file(payroll_run_id, session, format=format)
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Bank transfer file not found")
    
    # Read and return file
    with open(filepath, "rb") as f:
        content = f.read()
    
    media_type = "text/csv" if format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="bank_transfer_{payroll_run_id}.{format}"'}
    )

