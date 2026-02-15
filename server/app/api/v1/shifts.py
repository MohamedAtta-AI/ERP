from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from server.db import get_session
from server.db.models import Shift
from server.app.schemas.shift import ShiftCreate, ShiftRead, ShiftUpdate
from server.app.dependencies import require_admin, require_supervisor_or_admin

router = APIRouter()

@router.get("/", response_model=List[ShiftRead])
async def list_shifts(
    active_only: bool = True,
    session: Session = Depends(get_session),
    current_user=Depends(require_supervisor_or_admin),
):
    stmt = select(Shift)
    return session.exec(stmt).all()

@router.post("/", response_model=ShiftRead)
async def create_shift(
    shift_in: ShiftCreate,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    shift = Shift(**shift_in.model_dump())
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift

@router.put("/{shift_id}", response_model=ShiftRead)
async def update_shift(
    shift_id: UUID,
    shift_in: ShiftUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    shift = session.get(Shift, shift_id)
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    for k, v in shift_in.model_dump(exclude_unset=True).items():
        setattr(shift, k, v)
    
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift

@router.delete("/{shift_id}")
async def delete_shift(
    shift_id: UUID,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    shift = session.get(Shift, shift_id)
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    session.delete(shift)
    session.commit()
    return {"ok": True}
