"""
Tests — Rejection par rôle non autorisé pour chaque catégorie de helper (M4).
Vérifie que les endpoints migrés retournent 403 quand appelés par un rôle non autorisé.
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


def _create_user(db, email, role, school_id, is_active=True, is_approved=True):
    user = User(
        email=email, hashed_password=TEST_HASH, full_name=f"User {email}",
        role=role, is_active=is_active, is_approved=is_approved, school_id=school_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client, email):
    resp = client.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
    return resp.json().get("access_token")


@pytest.fixture(scope="function")
def setup():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
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

    users = {
        "super_admin": _create_user(db, "super@test.com", "super_admin", school.id),
        "pedagogical_admin": _create_user(db, "peda_admin@test.com", "pedagogical_admin", school.id),
        "admin_school": _create_user(db, "admin_school@test.com", "admin_school", school.id),
        "pedagogical_lead": _create_user(db, "peda_lead@test.com", "pedagogical_lead", school.id),
        "teacher": _create_user(db, "teacher@test.com", "teacher", school.id),
        "student": _create_user(db, "student@test.com", "student", school.id),
    }

    client = TestClient(app)
    tokens = {name: _login(client, u.email) for name, u in users.items()}

    yield client, db, users, tokens, school

    db.close()
    app.dependency_overrides.clear()


class TestPlatformAdminRejection:
    """require_platform_admin: rejecte teacher, admin_school, pedagogical_lead."""

    def test_teacher_rejected_from_list_settings(self, setup):
        """teacher ne peut PAS accéder aux settings (platform-only)."""
        client, _, _, tokens, _ = setup
        resp = client.get("/api/admin/settings", headers={"Authorization": f"Bearer {tokens['teacher']}"})
        assert resp.status_code == 403, f"teacher doit être rejeté de list_settings, reçu {resp.status_code}"

    def test_admin_school_rejected_from_broadcast(self, setup):
        """admin_school ne peut PAS envoyer de broadcast (platform-only)."""
        client, _, _, tokens, _ = setup
        resp = client.post("/api/admin/broadcast", json={"title": "t", "content": "c", "target_role": "all"},
                           headers={"Authorization": f"Bearer {tokens['admin_school']}"})
        assert resp.status_code == 403, f"admin_school doit être rejeté de broadcast, reçu {resp.status_code}"

    def test_pedagogical_lead_rejected_from_global_stats(self, setup):
        """pedagogical_lead ne peut PAS voir les stats globales (platform-only)."""
        client, _, _, tokens, _ = setup
        resp = client.get("/api/admin/stats/global", headers={"Authorization": f"Bearer {tokens['pedagogical_lead']}"})
        assert resp.status_code == 403, f"pedagogical_lead doit être rejeté de global_stats, reçu {resp.status_code}"

    def test_super_admin_allowed_list_settings(self, setup):
        """super_admin PEUT accéder aux settings (platform-level)."""
        client, _, _, tokens, _ = setup
        resp = client.get("/api/admin/settings", headers={"Authorization": f"Bearer {tokens['super_admin']}"})
        assert resp.status_code == 200, f"super_admin doit être autorisé, reçu {resp.status_code}"

    def test_pedagogical_admin_allowed_list_settings(self, setup):
        """pedagogical_admin PEUT accéder aux settings (platform-level)."""
        client, _, _, tokens, _ = setup
        resp = client.get("/api/admin/settings", headers={"Authorization": f"Bearer {tokens['pedagogical_admin']}"})
        assert resp.status_code == 200, f"pedagogical_admin doit être autorisé, reçu {resp.status_code}"


class TestSchoolAdminStrictRejection:
    """require_school_admin_strict: rejecte pedagogical_lead, teacher, student."""

    def test_pedagogical_lead_rejected_from_import_students(self, setup):
        """pedagogical_lead ne peut PAS importer des élèves (admin_school-only)."""
        client, _, _, tokens, _ = setup
        resp = client.post("/api/admin/import-students", json={"students": []},
                           headers={"Authorization": f"Bearer {tokens['pedagogical_lead']}"})
        assert resp.status_code == 403, f"pedagogical_lead doit être rejeté de import_students, reçu {resp.status_code}"

    def test_teacher_rejected_from_import_students(self, setup):
        """teacher ne peut PAS importer des élèves."""
        client, _, _, tokens, _ = setup
        resp = client.post("/api/admin/import-students", json={"students": []},
                           headers={"Authorization": f"Bearer {tokens['teacher']}"})
        assert resp.status_code == 403, f"teacher doit être rejeté de import_students, reçu {resp.status_code}"

    def test_admin_school_allowed_import_students(self, setup):
        """admin_school PEUT importer des élèves."""
        client, _, _, tokens, _ = setup
        # L'endpoint valide le body, on teste juste qu'il n'est PAS rejeté par le rôle
        resp = client.post("/api/admin/import-students", json={"students": []},
                           headers={"Authorization": f"Bearer {tokens['admin_school']}"})
        # Peut être 400 (validation) ou 200, mais PAS 403
        assert resp.status_code != 403, f"admin_school ne doit PAS être rejeté, reçu {resp.status_code}"

    def test_super_admin_rejected_from_import_students(self, setup):
        """super_admin est rejeté de import_students (school-only)."""
        client, _, _, tokens, _ = setup
        resp = client.post("/api/admin/import-students", json={"students": []},
                           headers={"Authorization": f"Bearer {tokens['super_admin']}"})
        assert resp.status_code == 403, f"super_admin doit être rejeté de import_students, reçu {resp.status_code}"


class TestRequireAdminUnchanged:
    """require_admin: teacher et student sont rejetés, admin_school et pedagogical_lead sont autorisés."""

    def test_teacher_rejected_from_list_courses(self, setup):
        """teacher ne peut PAS accéder à list_courses (admin endpoint)."""
        client, _, _, tokens, _ = setup
        resp = client.get("/api/admin/courses", headers={"Authorization": f"Bearer {tokens['teacher']}"})
        assert resp.status_code == 403, f"teacher doit être rejeté de list_courses, reçu {resp.status_code}"

    def test_student_rejected_from_list_users(self, setup):
        """student ne peut PAS accéder à list_users."""
        client, _, _, tokens, _ = setup
        resp = client.get("/api/admin/users", headers={"Authorization": f"Bearer {tokens['student']}"})
        assert resp.status_code == 403, f"student doit être rejeté de list_users, reçu {resp.status_code}"

    def test_admin_school_allowed_list_courses(self, setup):
        """admin_school PEUT accéder à list_courses."""
        client, _, _, tokens, _ = setup
        resp = client.get("/api/admin/courses", headers={"Authorization": f"Bearer {tokens['admin_school']}"})
        assert resp.status_code == 200, f"admin_school doit être autorisé, reçu {resp.status_code}"

    def test_pedagogical_lead_allowed_list_courses(self, setup):
        """pedagogical_lead PEUT accéder à list_courses."""
        client, _, _, tokens, _ = setup
        resp = client.get("/api/admin/courses", headers={"Authorization": f"Bearer {tokens['pedagogical_lead']}"})
        assert resp.status_code == 200, f"pedagogical_lead doit être autorisé, reçu {resp.status_code}"
