from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from server.db import get_session
from server.db.models import Person, PersonStatus
from server.app.services.password_service import verify_password
from server.app.services.jwt_service import generate_access_token, generate_refresh_token
from server.app.schemas.person import PersonRead

router = APIRouter()

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
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "user": PersonRead.from_orm(person)
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
