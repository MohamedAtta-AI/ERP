"""
Final Settlement API endpoints.

Admin only - handles final settlement calculations and approvals.
"""

from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.database import get_session
from server.app.dependencies import require_role
from server.app.services.final_settlement_service import (
    calculate_settlement,
    require_clearance,
    generate_settlement_payroll,
)
from server.db.models import Person

router = APIRouter()


class SettlementCalculateRequest(BaseModel):
    person_id: str
    termination_date: date


class SettlementResponse(BaseModel):
    person_id: str
    termination_date: date
    pro_rata_salary: float
    unused_leave_payout: float
    outstanding_liabilities: float
    gross_settlement: float
    net_settlement: float


@router.post("/calculate", response_model=SettlementResponse)
async def calculate_final_settlement(
    data: SettlementCalculateRequest,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Calculate final settlement for termination."""
    try:
        settlement_data = await calculate_settlement(
            data.person_id, data.termination_date, session
        )
        
        return SettlementResponse(
            person_id=settlement_data["person_id"],
            termination_date=settlement_data["termination_date"],
            pro_rata_salary=settlement_data["pro_rata_salary"],
            unused_leave_payout=settlement_data["unused_leave_payout"],
            outstanding_liabilities=settlement_data["outstanding_liabilities"],
            gross_settlement=settlement_data["gross_settlement"],
            net_settlement=settlement_data["net_settlement"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{person_id}/clearance")
async def check_clearance(
    person_id: str,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Check if person requires clearance before termination."""
    clearance = await require_clearance(person_id, session)
    return clearance


@router.post("/{settlement_id}/approve")
async def approve_settlement(
    settlement_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Approve final settlement and generate payroll."""
    # This would typically get settlement data from a Settlement table
    # For now, this is a placeholder
    raise HTTPException(status_code=501, detail="Settlement approval not yet implemented")


@router.get("/{settlement_id}")
async def get_settlement(
    settlement_id: UUID,
    current_user: Person = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Get settlement details."""
    # This would typically query a Settlement table
    # For now, this is a placeholder
    raise HTTPException(status_code=501, detail="Settlement retrieval not yet implemented")



