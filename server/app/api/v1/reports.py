"""
Reports API endpoints.

Admin only - handles report generation and export.
"""

from datetime import date
from typing import Optional
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.database import get_session
from server.app.dependencies import require_role
from server.app.services.report_service import (
    generate_attendance_report,
    generate_payroll_report,
    export_to_pdf,
    export_to_excel,
)
from server.db.models import Person

router = APIRouter()


@router.get("/attendance")
async def get_attendance_report(
    start_date: date,
    end_date: date,
    location_id: Optional[UUID] = None,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Generate attendance report."""
    report_data = await generate_attendance_report(
        start_date, end_date, session, location_id=location_id
    )
    return report_data


@router.get("/payroll")
async def get_payroll_report(
    payroll_run_id: Optional[UUID] = None,
    period_id: Optional[UUID] = None,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Generate payroll report."""
    report_data = await generate_payroll_report(
        session, payroll_run_id=payroll_run_id, period_id=period_id
    )
    return report_data


@router.get("/export")
async def export_report(
    report_type: str,  # "attendance" or "payroll"
    format: str,  # "pdf" or "excel"
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    location_id: Optional[UUID] = None,
    payroll_run_id: Optional[UUID] = None,
    period_id: Optional[UUID] = None,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Export report to PDF or Excel."""
    # Generate report data
    if report_type == "attendance":
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="start_date and end_date required for attendance report")
        report_data = await generate_attendance_report(
            start_date, end_date, session, location_id=location_id
        )
    elif report_type == "payroll":
        report_data = await generate_payroll_report(
            session, payroll_run_id=payroll_run_id, period_id=period_id
        )
    else:
        raise HTTPException(status_code=400, detail=f"Invalid report_type: {report_type}")
    
    # Generate file
    output_dir = Path("data/uploads/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"report_{report_type}_{date.today()}.{format}"
    output_path = output_dir / filename
    
    if format == "pdf":
        await export_to_pdf(report_data, output_path, template="default")
        media_type = "application/pdf"
    elif format == "excel":
        await export_to_excel(report_data, output_path)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}. Use 'pdf' or 'excel'")
    
    # Read and return file
    with open(output_path, "rb") as f:
        content = f.read()
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

