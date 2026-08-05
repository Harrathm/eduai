"""
Phase 1.1 — Password reset token leakage fix + email sending.

Test 1 (RED → GREEN): forgot-password endpoint must NEVER return the token in the response.
Test 2 (RED → GREEN): email service must be called with correct recipient and token.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models import User, School, PasswordResetToken
from app.core.security import get_password_hash

from tests.conftest import TEST_PASSWORD, TEST_HASH, _login, _auth


@pytest.fixture(scope="function")
def test_db(_base_session):
    db = _base_session
    school = School(name="Test School", slug="test-school", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    student = User(
        email="reset_test@test.com", hashed_password=TEST_HASH,
        full_name="Reset Test User", role="student", is_active=True,
        is_approved=True, school_id=school.id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    yield db, school, student


@pytest.fixture(scope="function")
def client(test_db):
    return TestClient(app)


# ============================================================
# TEST 1: Token must NEVER appear in the HTTP response
# ============================================================
def test_01_token_not_in_response(test_db, client):
    """BEFORE fix: response contained {"message": "...", "token": "xxx"}.
    AFTER fix: response contains only {"message": "..."} — no token field."""
    db, school, student = test_db

    resp = client.post("/auth/forgot-password", json={"email": "reset_test@test.com"})
    assert resp.status_code == 200
    data = resp.json()

    # CRITICAL: token must NOT be in the response
    assert "token" not in data, (
        f"SECURITY BREACH: token still in response! Keys: {list(data.keys())}"
    )

    # Message must be generic (same for existing and non-existing emails)
    assert "message" in data
    assert "réinitialisation" in data["message"].lower()


# ============================================================
# TEST 2: Email service is called with correct arguments
# ============================================================
def test_02_email_service_called(test_db, client):
    """Email sending must be triggered with the correct recipient and a valid token."""
    db, school, student = test_db

    with patch("app.services.email_service.send_password_reset_email", return_value=True) as mock_send:
        resp = client.post("/auth/forgot-password", json={"email": "reset_test@test.com"})
        assert resp.status_code == 200

        # Email service must have been called once
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args

        # Check recipient
        assert call_kwargs.kwargs["to_email"] == "reset_test@test.com"

        # Check token is a non-empty string
        token = call_kwargs.kwargs["reset_token"]
        assert isinstance(token, str)
        assert len(token) > 10

        # Check user name
        assert call_kwargs.kwargs["user_name"] == "Reset Test User"


# ============================================================
# TEST 3: Email failure does NOT break the endpoint
# ============================================================
def test_03_email_failure_still_returns_success(test_db, client):
    """Even if SMTP is down, the endpoint must return 200 with generic message."""
    db, school, student = test_db

    with patch("app.services.email_service.send_password_reset_email", return_value=False) as mock_send:
        resp = client.post("/auth/forgot-password", json={"email": "reset_test@test.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        # Same generic message whether email succeeds or fails
        assert "réinitialisation" in data["message"].lower()


# ============================================================
# TEST 4: Non-existing email returns same response (anti-enumeration)
# ============================================================
def test_04_non_existing_email_same_response(test_db, client):
    """Anti-enumeration: same response for existing and non-existing emails."""
    resp_existing = client.post("/auth/forgot-password", json={"email": "reset_test@test.com"})
    resp_missing = client.post("/auth/forgot-password", json={"email": "nonexistent@test.com"})

    assert resp_existing.status_code == 200
    assert resp_missing.status_code == 200
    assert resp_existing.json() == resp_missing.json()
