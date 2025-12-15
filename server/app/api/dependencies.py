"""Shared API dependencies."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db

# Database session dependency
async def get_database_session() -> AsyncSession:
    """Get database session."""
    async for session in get_db():
        yield session
