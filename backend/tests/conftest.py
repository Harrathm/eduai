"""
Test configuration and fixtures for EDUAI backend.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_db
from app.main import app
from app.models import User, School
from app.core.security import get_password_hash

TEST_PASSWORD = "password123"
TEST_HASH = get_password_hash(TEST_PASSWORD)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database using SQLite in-memory.

    Note: No cleanup needed for in-memory databases since the connection
    is destroyed when the engine is garbage-collected.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()

    school = School(name="Test School", slug="test-school", subscription_tier="free")
    db.add(school)
    db.commit()

    admin = User(
        email="test_admin@test.com",
        hashed_password=TEST_HASH,
        full_name="Test Admin",
        role="SUPER_ADMIN",
        is_active=True,
        is_approved=True,
        school_id=school.id,
    )
    db.add(admin)

    student = User(
        email="test_student@test.com",
        hashed_password=TEST_HASH,
        full_name="Test Student",
        role="STUDENT",
        is_active=True,
        is_approved=True,
        school_id=school.id,
    )
    db.add(student)
    db.commit()

    yield db, school, admin, student

    db.close()
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_db):
    """Return a test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def admin_token(client, test_db):
    """Return an auth token for the test admin."""
    response = client.post("/auth/login", data={"username": "test_admin@test.com", "password": TEST_PASSWORD})
    data = response.json()
    if "access_token" not in data:
        raise RuntimeError(f"Login failed: {response.status_code} {data}")
    return data["access_token"]


@pytest.fixture(scope="function")
def student_token(client, test_db):
    """Return an auth token for the test student."""
    response = client.post("/auth/login", data={"username": "test_student@test.com", "password": TEST_PASSWORD})
    data = response.json()
    if "access_token" not in data:
        raise RuntimeError(f"Login failed: {response.status_code} {data}")
    return data["access_token"]