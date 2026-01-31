from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from server.db import get_session
from server.db.models import Assignment
from server.app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate

router = APIRouter()

@router.get("/", response_model=List[AssignmentRead])
async def list_assignments(
    person_id: Optional[str] = None,
    location_id: Optional[UUID] = None, # Matches client calling it 'location_id' (which is site_id)
    session: Session = Depends(get_session),
):
    stmt = select(Assignment)
    if person_id:
        stmt = stmt.where(Assignment.person_id == person_id)
    if location_id:
        stmt = stmt.where(Assignment.site_id == location_id)
        
    return session.exec(stmt).all()

@router.post("/", response_model=AssignmentRead)
async def create_assignment(
    assign_in: AssignmentCreate,
    session: Session = Depends(get_session),
):
    # Optional: check if site/shift exist
    assign = Assignment(**assign_in.model_dump())
    session.add(assign)
    session.commit()
    session.refresh(assign)
    return assign

@router.put("/{assignment_id}", response_model=AssignmentRead)
async def update_assignment(
    assignment_id: UUID,
    assign_in: AssignmentUpdate,
    session: Session = Depends(get_session),
):
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    for k, v in assign_in.model_dump(exclude_unset=True).items():
        setattr(assignment, k, v)
        
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment

@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: UUID,
    session: Session = Depends(get_session),
):
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    session.delete(assignment)
    session.commit()
    return {"ok": True}
