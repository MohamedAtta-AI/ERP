"""
Pytest configuration and fixtures for testing.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_session
from app.main import app
from db.models import Person, Location, Shift
from sqlmodel import SQLModel
from app.services.password_service import hash_password


# Test database URL (in-memory SQLite for testing)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession):
    """Create a test client with database override."""
    async def override_get_session():
        yield db_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """Create a test admin user."""
    admin = Person(
        person_id="ADMIN1",
        full_name="Admin User",
        role="admin",
        status="active",
        password_hash=hash_password("test_password"),
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def supervisor_user(db_session: AsyncSession):
    """Create a test supervisor user."""
    supervisor = Person(
        person_id="SUPER1",
        full_name="Supervisor User",
        role="supervisor",
        status="active",
        password_hash=hash_password("test_password"),
    )
    db_session.add(supervisor)
    await db_session.commit()
    await db_session.refresh(supervisor)
    return supervisor


@pytest.fixture
async def worker_user(db_session: AsyncSession):
    """Create a test worker user."""
    worker = Person(
        person_id="WORKER1",
        full_name="Worker User",
        role="worker",
        status="active",
        password_hash=hash_password("test_password"),
    )
    db_session.add(worker)
    await db_session.commit()
    await db_session.refresh(worker)
    return worker


@pytest.fixture
async def test_location(db_session: AsyncSession):
    """Create a test location."""
    location = Location(
        name="Test Location",
        address="123 Test St",
        active=True,
    )
    db_session.add(location)
    await db_session.commit()
    await db_session.refresh(location)
    return location


@pytest.fixture
async def test_shift(db_session: AsyncSession):
    """Create a test shift."""
    shift = Shift(
        name="Day Shift",
        start_time="08:00:00",
        end_time="17:00:00",
        active=True,
    )
    db_session.add(shift)
    await db_session.commit()
    await db_session.refresh(shift)
    return shift

