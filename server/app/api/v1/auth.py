from typing import Annotated
import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from pydantic import BaseModel

from server.db import get_session
from server.db.models import Person, PersonStatus, Role
from server.app.services.password_service import verify_password, hash_password
from server.app.services.jwt_service import generate_access_token, generate_refresh_token
from server.app.schemas.person import PersonRead
from server.app.dependencies import require_auth
from server.config import config

router = APIRouter()


def _validate_new_password(password: str) -> str | None:
    if len(password or "") < 8:
        return "New password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return "New password must include at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "New password must include at least one lowercase letter."
    if not re.search(r"\d", password):
        return "New password must include at least one number."
    if not re.search(r"[^A-Za-z0-9]", password):
        return "New password must include at least one special character."
    return None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session)
):
    # Determine is using ID or Email? Form says 'username'.
    # We can support both.
    stmt = select(Person).where(
        (Person.id == form_data.username) | (Person.email == form_data.username)
    )
    person = session.exec(stmt).first()
    
    if not person or not verify_password(form_data.password, person.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if person.status != PersonStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )
        
    access_token = generate_access_token(person.id, role=person.role)
    refresh_token = generate_refresh_token(person.id)
    require_password_change = (
        person.role == Role.SUPERVISOR
        and verify_password(config.SUPERVISOR_DEFAULT_PASSWORD, person.password_hash)
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "user": PersonRead.model_validate(person),
        "require_password_change": require_password_change,
    }

# Refresh endpoint? Not explicitly requested but good to have
@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    session: Session = Depends(get_session)
):
    # Verify refresh token... need to implement verify in jwt_service or reuse
    from server.app.services.jwt_service import verify_token
    try:
        payload = verify_token(refresh_token, token_type="refresh")
        person_id = payload.get("sub")
        person = session.get(Person, person_id)
        if not person:
             raise HTTPException(status_code=401, detail="User not found")
             
        new_access = generate_access_token(person.id, person.role)
        return {"access_token": new_access, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: Person = Depends(require_auth),
    session: Session = Depends(get_session),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must be different from current password")

    policy_error = _validate_new_password(payload.new_password)
    if policy_error:
        raise HTTPException(status_code=400, detail=policy_error)

    current_user.password_hash = hash_password(payload.new_password)
    session.add(current_user)
    session.commit()
    return {"message": "Password updated successfully"}
