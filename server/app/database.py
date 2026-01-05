"""
Database connection and session management.

Uses SQLAlchemy async engine with PostgreSQL + pgvector.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from server.config import config

# Import models to ensure they're registered with SQLModel.metadata
# This must happen before init_db() is called
from server.db.models import (  # noqa: F401
    Person, Attendance, Role, Location, Shift,
    Skill, PersonSkill, SkillLocationPrice,
    Assignment, Document, OvertimeRequest,
    SalaryComponent, EmployeeComponent,
    PayrollPeriod, PayrollRun, PayrollRunEmployee, PayrollRunLine,
)


# Create async engine
engine = create_async_engine(
    config.DB_URL,
    echo=not config.PRODUCTION,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize database tables."""
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        # Create pgvector extension if not exists
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create all tables (models are already imported at module level)
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

