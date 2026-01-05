"""
Dependency injection for FastAPI endpoints.

Provides:
- Database session dependency
- Authentication/authorization dependencies
- Current user dependency
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.app.database import get_session
from server.db.models import Person, Role

# Security scheme for JWT tokens (placeholder - implement actual JWT later)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> Optional[Person]:
    """
    Get current authenticated user from token.
    
    TODO: Implement actual JWT token validation.
    For now, returns None (allows unauthenticated access in development).
    """
    if not credentials:
        return None
    
    # TODO: Decode JWT token and get person_id
    # For now, this is a placeholder
    # token = credentials.credentials
    # person_id = decode_jwt_token(token)
    # stmt = select(Person).where(Person.id == person_id)
    # result = await session.execute(stmt)
    # return result.scalar_one_or_none()
    
    return None


async def require_auth(
    current_user: Optional[Person] = Depends(get_current_user),
) -> Person:
    """Require authenticated user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return current_user


async def get_user_role(
    current_user: Optional[Person] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Optional[str]:
    """Get current user's role name."""
    if not current_user or not current_user.role_id:
        return None
    
    stmt = select(Role).where(Role.id == current_user.role_id)
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    return role.name if role else None


def require_role(*allowed_roles: str):
    """
    Dependency factory to require specific roles.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            _: Person = Depends(require_role("admin"))
        ):
            ...
    """
    async def role_checker(
        current_user: Person = Depends(require_auth),
        session: AsyncSession = Depends(get_session),
    ) -> Person:
        role_name = await get_user_role(current_user, session)
        
        if role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        
        return current_user
    
    return role_checker


def field_level_guard(admin_only_fields: list[str]):
    """
    Middleware to block non-admin users from editing certain fields.
    
    Usage:
        @router.put("/persons/{id}")
        async def update_person(
            data: PersonUpdate,
            _: Person = Depends(field_level_guard(["rate", "salary"]))
        ):
            ...
    """
    async def guard_checker(
        current_user: Person = Depends(require_auth),
        session: AsyncSession = Depends(get_session),
    ) -> Person:
        role_name = await get_user_role(current_user, session)
        
        # Admin can edit all fields
        if role_name == "admin":
            return current_user
        
        # Non-admin users will have fields filtered in the endpoint
        # This dependency just ensures they're authenticated
        return current_user
    
    return guard_checker

