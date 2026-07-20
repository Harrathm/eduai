"""
Tests — Verrouillage de compte (F3/F4) et is_active au login (M1).
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone, timedelta
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
def setup():
    """Create test DB, test user, and test client."""
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

    user = User(
        email="test_user@test.com",
        hashed_password=TEST_HASH,
        full_name="Test User",
        role="student",
        is_active=True,
        is_approved=True,
        school_id=school.id,
    )
    db.add(user)
    db.commit()

    client = TestClient(app)
    yield client, db, user

    db.close()
    app.dependency_overrides.clear()


class TestAccountLockout:
    """Vérifie le verrouillage de compte après 5 tentatives échouées."""

    def test_lockout_after_5_failed_attempts(self, setup):
        """5 mauvais mots de passe → 6e tentative (même avec BON mot de passe) rejetée 423."""
        client, db, user = setup

        # 5 tentatives échouées
        for i in range(5):
            response = client.post("/auth/login", data={
                "username": "test_user@test.com",
                "password": "wrong_password",
            })
            assert response.status_code == 401, f"Tentative {i+1}: attendu 401"

        # Vérifier que le compte est verrouillé
        db.refresh(user)
        assert user.locked_until is not None, "locked_until doit être défini après 5 échecs"
        assert user.locked_until > datetime.now(timezone.utc).replace(tzinfo=None), "locked_until doit être dans le futur"

        # 6e tentative avec le BON mot de passe → rejetée 423 (compte verrouillé)
        response = client.post("/auth/login", data={
            "username": "test_user@test.com",
            "password": TEST_PASSWORD,
        })
        assert response.status_code == 423, f"Attendu 423 (locked), reçu {response.status_code}"
        assert "locked" in response.json()["detail"].lower()

    def test_successful_login_resets_counter(self, setup):
        """4 échecs puis 1 succès → compteur remis à zéro, pas de lockout."""
        client, db, user = setup

        # 4 tentatives échouées
        for i in range(4):
            client.post("/auth/login", data={
                "username": "test_user@test.com",
                "password": "wrong_password",
            })

        db.refresh(user)
        assert user.failed_login_attempts == 4, "Compteur doit être à 4"

        # 1 tentative réussie
        response = client.post("/auth/login", data={
            "username": "test_user@test.com",
            "password": TEST_PASSWORD,
        })
        assert response.status_code == 200, f"Login doit réussir, reçu {response.status_code}"

        db.refresh(user)
        assert user.failed_login_attempts == 0, "Compteur doit être remis à 0"
        assert user.locked_until is None, "locked_until doit être None"

    def test_lockout_auto_expires(self, setup):
        """Un compte verrouillé se débloque après l'expiration du délai."""
        client, db, user = setup

        # Forcer un lockout avec lockout expiré (dans le passé, naive pour SQLite compat)
        user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        user.failed_login_attempts = 0
        db.commit()

        # Tentative avec bon mot de passe → doit réussir (lockout expiré)
        response = client.post("/auth/login", data={
            "username": "test_user@test.com",
            "password": TEST_PASSWORD,
        })
        assert response.status_code == 200, f"Login doit réussir après expiration, reçu {response.status_code}"


class TestLoginIsActive:
    """Vérifie qu'un compte désactivé (is_active=False) ne peut pas se connecter."""

    def test_inactive_user_gets_403(self, setup):
        client, db, user = setup

        # Désactiver le compte
        user.is_active = False
        db.commit()

        # Tentative de login → 403
        response = client.post("/auth/login", data={
            "username": "test_user@test.com",
            "password": TEST_PASSWORD,
        })
        assert response.status_code == 403, f"Attendu 403, reçu {response.status_code}"
        assert "deactivated" in response.json()["detail"].lower()

    def test_inactive_user_wrong_password_gets_401(self, setup):
        """Mauvais mot de passe sur un compte inactif → 401 (pas de fuite d'info sur l'état du compte)."""
        client, db, user = setup

        user.is_active = False
        db.commit()

        response = client.post("/auth/login", data={
            "username": "test_user@test.com",
            "password": "wrong_password",
        })
        # Le code vérifie le mot de passe AVANT is_active → 401
        assert response.status_code == 401, f"Attendu 401, reçu {response.status_code}"
