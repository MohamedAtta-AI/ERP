"""
Authentication API endpoints.

Handles login, token refresh, logout, and current user info.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.app.database import get_session
from server.app.dependencies import get_current_user, require_auth
from server.app.services.jwt_service import (
    generate_access_token,
    generate_refresh_token,
    verify_token,
)
from server.app.services.password_service import verify_password
from server.db.models import Person, Role

router = APIRouter()


class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    person_id: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Login with email/password or person_id.
    
    Returns JWT access and refresh tokens.
    """
    person = None
    
    # Support both email/password and person_id login
    if request.person_id:
        # Login by person_id (no password required for demo)
        stmt = select(Person).where(Person.id == request.person_id.upper())
        result = await session.execute(stmt)
        person = result.scalar_one_or_none()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid person ID"
            )
    elif request.email and request.password:
        # Login by email/password
        stmt = select(Person).where(Person.email == request.email)
        result = await session.execute(stmt)
        person = result.scalar_one_or_none()
        
        if not person or not person.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, person.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either (email and password) or person_id must be provided"
        )
    
    # Get role name
    role_name = None
    if person.role_id:
        role_stmt = select(Role).where(Role.id == person.role_id)
        role_result = await session.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        if role:
            role_name = role.name
    
    # Generate tokens
    access_token = generate_access_token(person.id, role_name)
    refresh_token = generate_refresh_token(person.id)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": person.id,
            "full_name": person.full_name,
            "email": person.email,
            "role": role_name,
        }
    )


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh(
    request: RefreshRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Refresh access token using refresh token.
    
    Validates refresh token and returns new access token.
    """
    try:
        payload = verify_token(request.refresh_token, "refresh")
        person_id = payload["sub"]
        
        # Get person and role
        stmt = select(Person).where(Person.id == person_id)
        result = await session.execute(stmt)
        person = result.scalar_one_or_none()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Get role name
        role_name = None
        if person.role_id:
            role_stmt = select(Role).where(Role.id == person.role_id)
            role_result = await session.execute(role_stmt)
            role = role_result.scalar_one_or_none()
            if role:
                role_name = role.name
        
        # Generate new access token
        access_token = generate_access_token(person.id, role_name)
        
        return RefreshResponse(access_token=access_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: Person = Depends(require_auth),
):
    """
    Logout and invalidate tokens.
    
    For now, just returns success. In production, you might want to
    maintain a token blacklist or update user record.
    """
    return {"message": "Logged out successfully"}


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_me(
    current_user: Person = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    """
    Get current user info.
    
    Returns authenticated user's information.
    """
    # Get role name
    role_name = None
    if current_user.role_id:
        from sqlalchemy import select
        from server.db.models import Role
        
        role_stmt = select(Role).where(Role.id == current_user.role_id)
        role_result = await session.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        if role:
            role_name = role.name
    
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": role_name,
        "department": current_user.department,
        "position": current_user.position,
    }

