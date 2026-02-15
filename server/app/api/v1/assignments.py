from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from server.db import get_session
from server.db.models import Assignment, Person, Role
from server.app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate
from server.app.dependencies import require_supervisor_or_admin

router = APIRouter()


def _can_manage_person(current_user: Person, person_id: str, session: Session) -> bool:
    if current_user.role == Role.ADMIN:
        return True
    if person_id == current_user.id:
        return True
    person = session.get(Person, person_id)
    return bool(person and person.role == Role.WORKER)

@router.get("/", response_model=List[AssignmentRead])
async def list_assignments(
    person_id: Optional[str] = None,
    location_id: Optional[UUID] = None, # Matches client calling it 'location_id' (which is site_id)
    session: Session = Depends(get_session),
    current_user: Person = Depends(require_supervisor_or_admin),
):
    stmt = select(Assignment)
    if current_user.role == Role.SUPERVISOR:
        worker_ids = session.exec(
            select(Person.id).where(Person.role == Role.WORKER)
        ).all()
        allowed_person_ids = list(set(worker_ids + [current_user.id]))
        stmt = stmt.where(Assignment.person_id.in_(allowed_person_ids))

    if person_id:
        if not _can_manage_person(current_user, person_id, session):
            raise HTTPException(status_code=403, detail="Not authorized for this person's assignments")
        stmt = stmt.where(Assignment.person_id == person_id)
    if location_id:
        stmt = stmt.where(Assignment.site_id == location_id)
        
    return session.exec(stmt).all()

@router.post("/", response_model=AssignmentRead)
async def create_assignment(
    assign_in: AssignmentCreate,
    session: Session = Depends(get_session),
    current_user: Person = Depends(require_supervisor_or_admin),
):
    if not _can_manage_person(current_user, assign_in.person_id, session):
        raise HTTPException(status_code=403, detail="Not authorized for this person's assignments")

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
    current_user: Person = Depends(require_supervisor_or_admin),
):
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if not assignment.person_id or not _can_manage_person(current_user, assignment.person_id, session):
        raise HTTPException(status_code=403, detail="Not authorized for this assignment")
        
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
    current_user: Person = Depends(require_supervisor_or_admin),
):
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if not assignment.person_id or not _can_manage_person(current_user, assignment.person_id, session):
        raise HTTPException(status_code=403, detail="Not authorized for this assignment")
    session.delete(assignment)
    session.commit()
    return {"ok": True}
