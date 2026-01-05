"""
Overtime Request API endpoints.
"""

from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.app.database import get_session
from server.app.dependencies import require_auth, require_role, get_user_role
from server.app.schemas.overtime import (
    OvertimeRequestCreate, OvertimeRequestRead, OvertimeRequestUpdate
)
from server.db.models import OvertimeRequest, Person, OvertimeRequestStatus

router = APIRouter()


@router.post("", response_model=OvertimeRequestRead, status_code=status.HTTP_201_CREATED)
async def create_overtime_request(
    data: OvertimeRequestCreate,
    current_user: Person = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new overtime request.
    
    Supervisor: Can create for workers under them.
    Admin: Can create for any person.
    """
    role_name = await get_user_role(current_user, session)
    
    # Supervisor can only create for workers under them
    if role_name == "supervisor":
        person_stmt = select(Person).where(Person.id == data.person_id)
        person_result = await session.execute(person_stmt)
        person = person_result.scalar_one_or_none()
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        if person.supervisor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors can only create overtime requests for workers under them"
            )
        
        data.created_by_person_id = current_user.id
    # Verify person exists
    person_stmt = select(Person).where(Person.id == data.person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    overtime_data = data.model_dump()
    if not overtime_data.get("created_by_person_id"):
        overtime_data["created_by_person_id"] = current_user.id
    
    overtime = OvertimeRequest(
        **overtime_data,
        status=OvertimeRequestStatus.PENDING,
    )
    session.add(overtime)
    await session.flush()
    await session.refresh(overtime)
    
    return OvertimeRequestRead(
        id=overtime.id,
        person_id=overtime.person_id,
        person_name=person.full_name,
        attendance_id=overtime.attendance_id,
        overtime_date=overtime.overtime_date,
        hours=overtime.hours,
        status=overtime.status.value,
        notes=overtime.notes,
        rejection_reason=overtime.rejection_reason,
        created_by_person_id=overtime.created_by_person_id,
        approved_by_person_id=overtime.approved_by_person_id,
        created_at=overtime.created_at,
        approved_at=overtime.approved_at,
    )


@router.get("", response_model=List[OvertimeRequestRead])
async def list_overtime_requests(
    person_id: str | None = None,
    status: str | None = None,
    current_user: Person = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """
    List overtime requests with optional filters.
    
    Supervisor: Can see requests for workers under them.
    Admin: Can see all requests.
    """
    role_name = await get_user_role(current_user, session)
    
    stmt = select(OvertimeRequest, Person).join(
        Person, OvertimeRequest.person_id == Person.id
    )
    
    # Supervisor can only see workers under them
    if role_name == "supervisor":
        stmt = stmt.where(Person.supervisor_id == current_user.id)
    stmt = select(OvertimeRequest, Person).join(
        Person, OvertimeRequest.person_id == Person.id
    )
    
    if person_id:
        stmt = stmt.where(OvertimeRequest.person_id == person_id)
    if status:
        stmt = stmt.where(OvertimeRequest.status == status)
    
    stmt = stmt.order_by(OvertimeRequest.created_at.desc())
    
    result = await session.execute(stmt)
    rows = result.all()
    
    return [
        OvertimeRequestRead(
            id=ot.id,
            person_id=ot.person_id,
            person_name=person.full_name,
            attendance_id=ot.attendance_id,
            overtime_date=ot.overtime_date,
            hours=ot.hours,
            status=ot.status.value,
            notes=ot.notes,
            rejection_reason=ot.rejection_reason,
            created_by_person_id=ot.created_by_person_id,
            approved_by_person_id=ot.approved_by_person_id,
            created_at=ot.created_at,
            approved_at=ot.approved_at,
        )
        for ot, person in rows
    ]


@router.get("/{overtime_id}", response_model=OvertimeRequestRead)
async def get_overtime_request(
    overtime_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get an overtime request by ID."""
    stmt = select(OvertimeRequest, Person).join(
        Person, OvertimeRequest.person_id == Person.id
    ).where(OvertimeRequest.id == overtime_id)
    
    result = await session.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Overtime request not found")
    
    ot, person = row
    
    return OvertimeRequestRead(
        id=ot.id,
        person_id=ot.person_id,
        person_name=person.full_name,
        attendance_id=ot.attendance_id,
        overtime_date=ot.overtime_date,
        hours=ot.hours,
        status=ot.status.value,
        notes=ot.notes,
        rejection_reason=ot.rejection_reason,
        created_by_person_id=ot.created_by_person_id,
        approved_by_person_id=ot.approved_by_person_id,
        created_at=ot.created_at,
        approved_at=ot.approved_at,
    )


@router.put("/{overtime_id}/approve", response_model=OvertimeRequestRead)
async def approve_overtime_request(
    overtime_id: UUID,
    data: OvertimeRequestUpdate,
    current_user: Person = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """
    Approve or reject an overtime request.
    
    Supervisor: Can approve for workers under them.
    Admin: Can approve any request.
    """
    role_name = await get_user_role(current_user, session)
    
    stmt = select(OvertimeRequest, Person).join(
        Person, OvertimeRequest.person_id == Person.id
    ).where(OvertimeRequest.id == overtime_id)
    
    result = await session.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Overtime request not found")
    
    overtime, person = row
    
    # Supervisor can only approve for workers under them
    if role_name == "supervisor":
        if person.supervisor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors can only approve overtime requests for workers under them"
            )
    stmt = select(OvertimeRequest).where(OvertimeRequest.id == overtime_id)
    result = await session.execute(stmt)
    overtime = result.scalar_one_or_none()
    
    if not overtime:
        raise HTTPException(status_code=404, detail="Overtime request not found")
    
    if overtime.status != OvertimeRequestStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Overtime request is already {overtime.status.value}",
        )
    
    # Update status
    if data.status == "approved":
        overtime.status = OvertimeRequestStatus.APPROVED
        overtime.approved_by_person_id = current_user.id
        overtime.approved_at = datetime.utcnow()
    elif data.status == "rejected":
        overtime.status = OvertimeRequestStatus.REJECTED
        overtime.rejection_reason = data.rejection_reason
    
    session.add(overtime)
    await session.flush()
    await session.refresh(overtime)
    
    # Get person for response
    person_stmt = select(Person).where(Person.id == overtime.person_id)
    person_result = await session.execute(person_stmt)
    person = person_result.scalar_one()
    
    return OvertimeRequestRead(
        id=overtime.id,
        person_id=overtime.person_id,
        person_name=person.full_name,
        attendance_id=overtime.attendance_id,
        overtime_date=overtime.overtime_date,
        hours=overtime.hours,
        status=overtime.status.value,
        notes=overtime.notes,
        rejection_reason=overtime.rejection_reason,
        created_by_person_id=overtime.created_by_person_id,
        approved_by_person_id=overtime.approved_by_person_id,
        created_at=overtime.created_at,
        approved_at=overtime.approved_at,
    )

