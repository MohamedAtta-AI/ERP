from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from server.db import get_session
from server.db.models import Person, Role
from server.app.services.jwt_service import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> Person:
    try:
        payload = verify_token(token)
        person_id = payload.get("sub")
        if not person_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    person = session.get(Person, person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return person

def require_auth(current_user: Person = Depends(get_current_user)) -> Person:
    return current_user

def require_admin(current_user: Person = Depends(get_current_user)) -> Person:
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user

def require_supervisor_or_admin(current_user: Person = Depends(get_current_user)) -> Person:
    if current_user.role not in [Role.ADMIN, Role.SUPERVISOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor or Admin privileges required",
        )
    return current_user
