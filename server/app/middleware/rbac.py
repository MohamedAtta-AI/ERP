"""
Role-Based Access Control (RBAC) middleware.

Provides decorators and utilities for enforcing role-based permissions
and field-level access control.
"""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server.db.models import Person, Role


async def get_role_name(person: Person, session: AsyncSession) -> Optional[str]:
    """Get role name for a person."""
    if not person or not person.role_id:
        return None
    
    stmt = select(Role).where(Role.id == person.role_id)
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    return role.name if role else None


def require_role(roles: List[str]):
    """
    Decorator factory for requiring specific roles.
    
    This is a helper that can be used with FastAPI dependencies.
    See server/app/dependencies.py for the actual dependency implementation.
    """
    def decorator(func):
        # The actual enforcement happens in dependencies.py
        # This is just for documentation/type hints
        return func
    return decorator


def filter_admin_only_fields(
    data: dict,
    admin_only_fields: List[str],
    current_user_role: Optional[str],
) -> dict:
    """
    Filter out admin-only fields from update data for non-admin users.
    
    Args:
        data: Dictionary of fields to update
        admin_only_fields: List of field names that only admins can edit
        current_user_role: Current user's role name
    
    Returns:
        Filtered dictionary with admin-only fields removed if user is not admin
    """
    if current_user_role == "admin":
        return data
    
    filtered = {k: v for k, v in data.items() if k not in admin_only_fields}
    
    # Warn if fields were filtered
    removed = set(data.keys()) - set(filtered.keys())
    if removed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only admins can edit these fields: {', '.join(removed)}",
        )
    
    return filtered


# Common admin-only fields for different models
ADMIN_ONLY_FIELDS = {
    "person": ["rate", "salary", "position", "department"],
    "assignment": ["rate", "title"],
    "skill_location_price": ["price"],
    "employee_component": ["value_override"],
    "payroll_run": ["status", "approved_by_person_id"],
}

