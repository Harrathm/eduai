"""
Shared test configuration and fixtures for EDUAI backend.

Provides:
  - _base_engine / _base_session  — reusable SQLite in-memory engine
  - test_db                        — generic (school, admin, student) tuple
  - client                         — FastAPI TestClient wired to the test DB
  - admin_token / student_token    — pre-authenticated JWT tokens
  - _login / _auth                 — helpers for ad-hoc logins

Test files that need domain-specific data should create their own fixture
that depends on _base_engine (or _base_session) and yields the extra objects
they need.  This avoids duplicating the engine/session/override boilerplate.
"""
import os

# ---------------------------------------------------------------------------
# Environment — must be set before any app import
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Low-level engine / session (shared across all tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def _base_engine():
    """Session-scoped SQLite in-memory engine shared by all tests."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope="function")
def _base_session(_base_engine):
    """Function-scoped session with full data cleanup between tests."""
    Session = sessionmaker(bind=_base_engine)
    session = Session()

    # Clean all data from every table to isolate tests
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    # Wire FastAPI dependency override
    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    yield session
    app.dependency_overrides.clear()
    session.close()


# ---------------------------------------------------------------------------
# Generic test_db fixture — (db, school, admin, student)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def test_db(_base_session):
    """Generic test database with a school, admin, and student.

    If your test needs different data (teacher, parent, packs, etc.),
    create your own fixture that depends on ``_base_session`` and yields
    whatever tuple your tests expect.
    """
    db = _base_session

    school = School(name="Test School", slug="test-school", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    admin = User(
        email="test_admin@test.com",
        hashed_password=TEST_HASH,
        full_name="Test Admin",
        role="super_admin",
        is_active=True,
        is_approved=True,
        school_id=school.id,
    )
    db.add(admin)

    student = User(
        email="test_student@test.com",
        hashed_password=TEST_HASH,
        full_name="Test Student",
        role="student",
        is_active=True,
        is_approved=True,
        school_id=school.id,
    )
    db.add(student)
    db.commit()
    db.refresh(admin)
    db.refresh(student)

    yield db, school, admin, student


# ---------------------------------------------------------------------------
# FastAPI TestClient
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client(test_db):
    """Return a TestClient wired to the current test database."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Pre-authenticated tokens
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def admin_token(client, test_db):
    """JWT token for the generic admin user."""
    resp = client.post(
        "/auth/login",
        data={"username": "test_admin@test.com", "password": TEST_PASSWORD},
    )
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Login failed: {resp.status_code} {data}")
    return data["access_token"]


@pytest.fixture(scope="function")
def student_token(client, test_db):
    """JWT token for the generic student user."""
    resp = client.post(
        "/auth/login",
        data={"username": "test_student@test.com", "password": TEST_PASSWORD},
    )
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Login failed: {resp.status_code} {data}")
    return data["access_token"]


# ---------------------------------------------------------------------------
# Login / auth helpers (for tests that create their own users)
# ---------------------------------------------------------------------------

def _login(client, email, password=TEST_PASSWORD):
    """Log in and return the access token string (or None on failure)."""
    resp = client.post("/auth/login", data={"username": email, "password": password})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def _auth(token):
    """Return an Authorization header dict for the given token."""
    return {"Authorization": f"Bearer {token}"}
