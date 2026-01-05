"""
Database connection and session management.

Uses SQLAlchemy async engine with PostgreSQL + pgvector.
"""

import asyncio
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
    SalaryAdvance, Loan, PayrollGroup, Payslip, AuditLog,
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
    """Initialize database tables using Alembic migrations."""
    from sqlalchemy import text
    from alembic.config import Config
    from alembic import command
    from alembic.script import ScriptDirectory
    
    async with engine.begin() as conn:
        # Create pgvector extension if not exists
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    
    # Run Alembic migrations
    import os
    from pathlib import Path
    # alembic.ini is in the project root (parent of server/)
    project_root = Path(__file__).parent.parent.parent
    alembic_ini_path = project_root / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    
    # Check if migrations are up to date
    # Run Alembic migrations synchronously (Alembic commands are sync)
    # We need to run this in a thread to avoid blocking the async event loop
    import concurrent.futures
    try:
        def run_migrations():
            script = ScriptDirectory.from_config(alembic_cfg)
        head = script.get_current_head()
        command.upgrade(alembic_cfg, "head")
        
        # Run migrations in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, run_migrations)
    except Exception as e:
        # If no migrations exist yet, that's okay - they'll be created
        print(f"Note: Alembic migrations not yet set up: {e}")
        # Fallback to create_all for initial setup
        async with engine.begin() as conn:
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

