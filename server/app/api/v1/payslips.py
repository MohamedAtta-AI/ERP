"""
Payslips API endpoints.

Handles payslip generation and download.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from server.app.database import get_session
from server.app.dependencies import require_auth, require_role, get_user_role
from server.app.services.payslip_service import generate_payslip, get_payslip_data
from server.db.models import Payslip, PayrollRunEmployee, Person

router = APIRouter()


class PayslipResponse(BaseModel):
    id: UUID
    payroll_run_employee_id: UUID
    person_id: str
    person_name: str
    generated_at: str
    pdf_url_ar: Optional[str] = None
    pdf_url_en: Optional[str] = None
    language: str
    
    class Config:
        from_attributes = True


@router.get("/{person_id}", response_model=List[PayslipResponse])
async def get_payslips(
    person_id: str,
    current_user: Person = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """
    Get payslips for a person.
    
    Worker: Can only view own payslips (person_id must == current_user.id)
    Admin: Can view any person's payslips
    """
    # RBAC check
    role_name = await get_user_role(current_user, session)
    
    if role_name == "worker":
        if person_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workers can only view their own payslips"
            )
    
    stmt = select(Payslip).where(Payslip.person_id == person_id)
    result = await session.execute(stmt)
    payslips = result.scalars().all()
    
    # Get person name
    person_stmt = select(Person).where(Person.id == person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    person_name = person.full_name if person else "Unknown"
    
    return [
        PayslipResponse(
            id=ps.id,
            payroll_run_employee_id=ps.payroll_run_employee_id,
            person_id=ps.person_id,
            person_name=person_name,
            generated_at=ps.generated_at.isoformat(),
            pdf_url_ar=ps.pdf_url_ar,
            pdf_url_en=ps.pdf_url_en,
            language=ps.language,
        )
        for ps in payslips
    ]


@router.get("/{payslip_id}/download")
async def download_payslip(
    payslip_id: UUID,
    language: str = "ar",
    current_user: Person = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """Download payslip PDF."""
    stmt = select(Payslip).where(Payslip.id == payslip_id)
    result = await session.execute(stmt)
    payslip = result.scalar_one_or_none()
    
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    # RBAC check
    role_name = await get_user_role(current_user, session)
    
    if role_name == "worker":
        if payslip.person_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workers can only download their own payslips"
            )
    
    # Get PDF URL
    pdf_url = payslip.pdf_url_ar if language == "ar" else payslip.pdf_url_en
    
    if not pdf_url:
        raise HTTPException(status_code=404, detail=f"Payslip PDF not found for language: {language}")
    
    # Read and return file
    from pathlib import Path
    pdf_path = Path(pdf_url)
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Payslip PDF file not found")
    
    with open(pdf_path, "rb") as f:
        content = f.read()
    
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="payslip_{payslip_id}_{language}.pdf"'}
    )


@router.post("/generate")
async def generate_payslips(
    payroll_run_id: UUID,
    language: str = "ar",
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Generate payslips for a payroll run (Admin only)."""
    # Get all payroll run employees
    stmt = select(PayrollRunEmployee).where(
        PayrollRunEmployee.payroll_run_id == payroll_run_id
    )
    result = await session.execute(stmt)
    employees = result.scalars().all()
    
    generated = []
    for emp in employees:
        try:
            payslip = await generate_payslip(emp.id, session, language=language)
            generated.append(payslip.id)
        except Exception as e:
            # Log error but continue
            print(f"Error generating payslip for employee {emp.id}: {e}")
    
    return {
        "payroll_run_id": payroll_run_id,
        "language": language,
        "generated_count": len(generated),
        "payslip_ids": generated,
    }

