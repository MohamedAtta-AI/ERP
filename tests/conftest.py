"""
Pytest configuration and fixtures for OnTime ERP tests.

This module provides:
- Test database setup with SQLite for isolation
- Async HTTP client for API testing
- Factory fixtures for creating test data
- Common utilities and mocks
"""

import os
import asyncio
from datetime import date, datetime, time
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from faker import Faker
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

# Set test environment before importing app modules
os.environ["PRODUCTION"] = "false"
os.environ["DB_URL"] = "sqlite://"  # In-memory SQLite for tests


# ============================================================
# Database Fixtures
# ============================================================


@pytest.fixture(scope="session")
def sync_engine():
    """Create a synchronous SQLite engine for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(sync_engine) -> Generator[Session, None, None]:
    """Provide a database session for tests with automatic rollback."""
    connection = sync_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ============================================================
# Faker Fixture
# ============================================================


@pytest.fixture(scope="session")
def faker() -> Faker:
    """Provide a Faker instance for generating test data."""
    fake = Faker()
    Faker.seed(12345)  # Reproducible test data
    return fake


# ============================================================
# Test Data Factories
# ============================================================


class PersonFactory:
    """Factory for creating Person test data."""

    def __init__(self, faker: Faker):
        self.faker = faker

    def build(self, **kwargs) -> dict:
        """Build a Person data dictionary without saving to DB."""
        import random
        import string

        defaults = {
            "id": "".join(random.choices(string.ascii_uppercase + string.digits, k=6)),
            "full_name": self.faker.name(),
            "identity_number": self.faker.ssn(),
            "dob": self.faker.date_of_birth(minimum_age=18, maximum_age=65),
            "sex": random.choice(["M", "F"]),
            "phone": self.faker.phone_number()[:15],
            "status": "active",
        }
        defaults.update(kwargs)
        return defaults


class LocationFactory:
    """Factory for creating Location test data."""

    def __init__(self, faker: Faker):
        self.faker = faker

    def build(self, **kwargs) -> dict:
        """Build a Location data dictionary without saving to DB."""
        defaults = {
            "id": uuid4(),
            "name": self.faker.company(),
            "city": self.faker.city(),
        }
        defaults.update(kwargs)
        return defaults


class ShiftFactory:
    """Factory for creating Shift test data."""

    def __init__(self, faker: Faker):
        self.faker = faker

    def build(self, **kwargs) -> dict:
        """Build a Shift data dictionary without saving to DB."""
        defaults = {
            "id": uuid4(),
            "starts_at": time(8, 0),
            "ends_at": time(17, 0),
        }
        defaults.update(kwargs)
        return defaults


class SkillFactory:
    """Factory for creating Skill test data."""

    def __init__(self, faker: Faker):
        self.faker = faker

    def build(self, **kwargs) -> dict:
        """Build a Skill data dictionary without saving to DB."""
        defaults = {
            "id": uuid4(),
            "name": self.faker.job(),
        }
        defaults.update(kwargs)
        return defaults


@pytest.fixture
def person_factory(faker) -> PersonFactory:
    """Provide a PersonFactory instance."""
    return PersonFactory(faker)


@pytest.fixture
def location_factory(faker) -> LocationFactory:
    """Provide a LocationFactory instance."""
    return LocationFactory(faker)


@pytest.fixture
def shift_factory(faker) -> ShiftFactory:
    """Provide a ShiftFactory instance."""
    return ShiftFactory(faker)


@pytest.fixture
def skill_factory(faker) -> SkillFactory:
    """Provide a SkillFactory instance."""
    return SkillFactory(faker)


# ============================================================
# Face Recognition Fixtures
# ============================================================


@pytest.fixture
def sample_embedding():
    """Provide a sample 128-dimensional face embedding."""
    import numpy as np

    np.random.seed(42)
    embedding = np.random.randn(128).astype(np.float32)
    # Normalize to unit length (as real embeddings would be)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding


@pytest.fixture
def similar_embedding(sample_embedding):
    """Provide an embedding similar to sample_embedding (high similarity > 0.95)."""
    import numpy as np

    np.random.seed(43)
    # Use very small noise to ensure high similarity (> 0.95)
    noise = np.random.randn(128).astype(np.float32) * 0.02
    similar = sample_embedding + noise
    similar = similar / np.linalg.norm(similar)
    return similar


@pytest.fixture
def different_embedding():
    """Provide an embedding different from sample_embedding (low similarity)."""
    import numpy as np

    np.random.seed(999)
    embedding = np.random.randn(128).astype(np.float32)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding


# ============================================================
# Mock Image Fixtures
# ============================================================


@pytest.fixture
def mock_face_image():
    """Provide a mock face image as numpy array."""
    import numpy as np

    # Create a simple 224x224x3 RGB image (typical face input size)
    return np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)


# ============================================================
# Date/Time Fixtures
# ============================================================


@pytest.fixture
def today() -> date:
    """Provide today's date."""
    return date.today()


@pytest.fixture
def now() -> datetime:
    """Provide current datetime."""
    return datetime.now()


@pytest.fixture
def morning_shift() -> dict:
    """Provide morning shift times (8:00 - 17:00)."""
    return {
        "starts_at": time(8, 0),
        "ends_at": time(17, 0),
    }


@pytest.fixture
def night_shift() -> dict:
    """Provide night shift times (22:00 - 06:00)."""
    return {
        "starts_at": time(22, 0),
        "ends_at": time(6, 0),
    }
