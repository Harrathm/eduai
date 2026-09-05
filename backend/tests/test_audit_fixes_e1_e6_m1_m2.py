"""
Tests des corrections d'audit :
  - E1 : tier du dashboard = tier BRUT du pack de l'Abonnement actif (source de vérité unique)
  - E6 : dashboard expose free_lessons_used_this_trimester / free_lessons_limit (compte serveur)
  - M1 : POST /auth/logout révoque les refresh tokens en base
  - M2 : PUT /auth/me/password (ancien vérifié, nouveau hashé, refresh tokens révoqués)
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

from datetime import datetime, timedelta, timezone

import pytest

from app.models import (
    User, School, PackDefinition, Abonnement,
    Course, CourseEnrollment, LessonProgress,
)
from tests.conftest import TEST_PASSWORD, _auth as _auth_header


@pytest.fixture(scope="function")
def golden_student_db(_base_session):
    """Élève avec un Abonnement actif sur un pack Golden."""
    db = _base_session
    school = School(name="Golden School", slug="golden-school", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    student = User(
        email="golden_student@test.com",
        hashed_password=None,
        full_name="Golden Student",
        role="student",
        is_active=True,
        is_approved=True,
        school_id=school.id,
        niveau_scolaire="4ème",
    )
    student.hashed_password = TEST_PASSWORD + "_hash"
    from app.core.security import get_password_hash
    student.hashed_password = get_password_hash(TEST_PASSWORD)
    db.add(student)
    db.commit()
    db.refresh(student)

    pack = PackDefinition(
        nom="Pack Golden",
        tier="Golden",
        niveau_scolaire="4ème",
        prix_tnd=49.9,
        est_actif=True,
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)

    now = datetime.now(timezone.utc)
    abo = Abonnement(
        user_id=student.id,
        pack_id=pack.id,
        statut="actif",
        debut=now - timedelta(days=10),
        fin=now + timedelta(days=355),
    )
    db.add(abo)
    db.commit()

    return db, school, student, pack, abo


# ──────────────────────────── E1 ────────────────────────────

class TestE1TierFromAbonnement:
    def test_tier_is_raw_pack_tier(self, client, golden_student_db):
        """Un élève avec Abonnement Golden → dashboard.tier == 'golden'."""
        _, _, student, pack, _ = golden_student_db
        resp = client.post("/auth/login", data={
            "username": student.email, "password": TEST_PASSWORD,
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        resp = client.get("/api/learner/dashboard", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "golden"          # ← tier brut du pack (E1)
        assert data["legacy_tier"] == "etablissement"  # mapping legacy interne

    def test_no_abonnement_means_gratuit(self, client, test_db, student_token):
        """Élève sans Abonnement → dashboard.tier == 'gratuit'."""
        resp = client.get("/api/learner/dashboard", headers=_auth_header(student_token))
        assert resp.status_code == 200
        assert resp.json()["tier"] == "gratuit"

    def test_expired_abonnement_ignored(self, client, golden_student_db):
        """Un abonnement expiré ne compte pas → tier retombe à 'gratuit'."""
        db, school, student, pack, abo = golden_student_db
        abo.fin = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()

        resp = client.post("/auth/login", data={
            "username": student.email, "password": TEST_PASSWORD,
        })
        token = resp.json()["access_token"]
        resp = client.get("/api/learner/dashboard", headers=_auth_header(token))
        assert resp.json()["tier"] == "gratuit"


# ──────────────────────────── E6 ────────────────────────────

class TestE6QuotaServeur:
    def test_dashboard_exposes_quota_fields(self, client, test_db, student_token):
        """Le dashboard expose le quota réel calculé serveur."""
        resp = client.get("/api/learner/dashboard", headers=_auth_header(student_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["free_lessons_used_this_trimester"] == 0
        assert data["free_lessons_limit"] == 3

    def test_quota_counts_completed_lessons_this_trimester(self, client, test_db, student_token):
        """2 leçons complétées dans le trimestre → used == 2 (pas lessons_completed global)."""
        db, school, admin, student = test_db

        course = Course(
            title="Cours Quota", description="", niveau_scolaire="6ème",
            school_id=school.id, author_id=admin.id, status="published",
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        enrollment = CourseEnrollment(student_id=student.id, course_id=course.id)
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        start, end = None, None
        now = datetime.now(timezone.utc)
        y, m = now.year, now.month
        if m >= 9:
            start = datetime(y, 9, 1); end = datetime(y + 1, 1, 1)
        elif m <= 3:
            start = datetime(y, 1, 1); end = datetime(y, 4, 1)
        else:
            start = datetime(y, 4, 1); end = datetime(y, 9, 1)

        for lid in (900101, 900102):
            db.add(LessonProgress(
                enrollment_id=enrollment.id, lesson_id=lid,
                status="completed",
                completed_at=start + timedelta(days=5),
            ))
        # Une leçon complétée HORS trimestre (année passée) → ne doit PAS compter
        db.add(LessonProgress(
            enrollment_id=enrollment.id, lesson_id=900103,
            status="completed",
            completed_at=datetime(2020, 1, 15),
        ))
        db.commit()

        resp = client.get("/api/learner/dashboard", headers=_auth_header(student_token))
        data = resp.json()
        assert data["free_lessons_used_this_trimester"] == 2


# ──────────────────────────── M1 ────────────────────────────

class TestM1LogoutRevokesRefreshTokens:
    def test_logout_then_refresh_fails(self, client, test_db):
        """Après POST /auth/logout, l'ancien refresh token est refusé (401)."""
        login = client.post("/auth/login", data={
            "username": "test_student@test.com", "password": TEST_PASSWORD,
        })
        assert login.status_code == 200
        access = login.json()["access_token"]
        refresh = login.json()["refresh_token"]

        out = client.post("/auth/logout", json={}, headers=_auth_header(access))
        assert out.status_code == 200
        assert out.json()["revoked_sessions"] >= 1

        reuse = client.post("/auth/refresh-token", json={"refresh_token": refresh})
        assert reuse.status_code == 401

    def test_logout_requires_auth(self, client, test_db):
        resp = client.post("/auth/logout", json={})
        assert resp.status_code in (401, 403)


# ──────────────────────────── M2 ────────────────────────────

NEW_PASSWORD = "NewPassword123"


class TestM2ChangePassword:
    def _login(self, client, password):
        return client.post("/auth/login", data={
            "username": "test_student@test.com", "password": password,
        })

    def test_wrong_old_password_rejected(self, client, test_db, student_token):
        resp = client.put("/auth/me/password", json={
            "old_password": "WrongOld123",
            "new_password": NEW_PASSWORD,
        }, headers=_auth_header(student_token))
        assert resp.status_code == 400

    def test_weak_new_password_rejected(self, client, test_db, student_token):
        resp = client.put("/auth/me/password", json={
            "old_password": TEST_PASSWORD,
            "new_password": "court1",
        }, headers=_auth_header(student_token))
        assert resp.status_code == 422

    def test_same_as_old_rejected(self, client, test_db, student_token):
        resp = client.put("/auth/me/password", json={
            "old_password": TEST_PASSWORD,
            "new_password": TEST_PASSWORD,
        }, headers=_auth_header(student_token))
        assert resp.status_code == 400

    def test_change_success_and_login_with_new(self, client, test_db, student_token):
        resp = client.put("/auth/me/password", json={
            "old_password": TEST_PASSWORD,
            "new_password": NEW_PASSWORD,
        }, headers=_auth_header(student_token))
        assert resp.status_code == 200

        old_login = self._login(client, TEST_PASSWORD)
        assert old_login.status_code == 401

        new_login = self._login(client, NEW_PASSWORD)
        assert new_login.status_code == 200

    def test_change_revokes_refresh_tokens(self, client, test_db):
        """Changement de mot de passe → les autres sessions ne peuvent plus se rafraîchir."""
        login = client.post("/auth/login", data={
            "username": "test_student@test.com", "password": TEST_PASSWORD,
        })
        access = login.json()["access_token"]
        refresh = login.json()["refresh_token"]

        change = client.put("/auth/me/password", json={
            "old_password": TEST_PASSWORD,
            "new_password": NEW_PASSWORD,
        }, headers=_auth_header(access))
        assert change.status_code == 200

        reuse = client.post("/auth/refresh-token", json={"refresh_token": refresh})
        assert reuse.status_code == 401

    def test_change_requires_auth(self, client, test_db):
        resp = client.put("/auth/me/password", json={
            "old_password": TEST_PASSWORD, "new_password": NEW_PASSWORD,
        })
        assert resp.status_code in (401, 403)
