"""
Tests for governance features: Context Switcher, ABAC, CMS Versioning, Bulk Seats.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import (
    User, School, Course, Module, Lesson, CourseStatus,
    Abonnement, PackDefinition, BulkSeatVoucher, CourseEnrollment,
)
from app.core.security import get_password_hash

TEST_PASSWORD = "password123"
TEST_HASH = get_password_hash(TEST_PASSWORD)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh SQLite in-memory database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    yield session
    app.dependency_overrides.clear()
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Return a TestClient wired to the current test database."""
    return TestClient(app)


def _create_user(db, email, role, school_id, roles=None, niveau_scolaire=None):
    user = User(
        email=email,
        hashed_password=TEST_HASH,
        full_name=f"User {email}",
        role=role,
        roles=roles or [role],
        active_context_role=role,
        is_active=True,
        is_approved=True,
        school_id=school_id,
        niveau_scolaire=niveau_scolaire,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_school(db):
    school = School(name="Test School", slug="test-school", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def _login(client, email, password=TEST_PASSWORD):
    resp = client.post("/auth/login", data={"username": email, "password": password})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# Tests: Context Switcher
# ============================================================

class TestContextSwitcher:
    def test_switch_context_valid_role(self, client, db_session):
        """Test that switching to a valid role returns 200 and a new JWT."""
        school = _create_school(db_session)
        user = _create_user(
            db_session,
            "multi@test.com",
            "admin_school",
            school.id,
            roles=["admin_school", "pedagogical_lead"],
        )

        token = _login(client, "multi@test.com")
        assert token is not None

        # Switch to pedagogical_lead
        resp = client.post(
            "/auth/switch-context",
            json={"role": "pedagogical_lead"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

        # Verify the new token has the correct active_role
        import jwt as pyjwt
        from app.core.config import get_settings
        settings = get_settings()
        payload = pyjwt.decode(data["access_token"], settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["active_role"] == "pedagogical_lead"

    def test_switch_context_invalid_role(self, client, db_session):
        """Test that switching to an invalid role returns 403."""
        school = _create_school(db_session)
        user = _create_user(
            db_session,
            "single@test.com",
            "student",
            school.id,
            roles=["student"],
        )

        token = _login(client, "single@test.com")
        assert token is not None

        # Try to switch to admin_school (not in user's roles)
        resp = client.post(
            "/auth/switch-context",
            json={"role": "admin_school"},
            headers=_auth(token),
        )
        assert resp.status_code == 403
        assert "not in your roles" in resp.json()["detail"]

    def test_switch_context_updates_user_record(self, client, db_session):
        """Test that switch-context updates active_context_role in the database."""
        school = _create_school(db_session)
        user = _create_user(
            db_session,
            "updater@test.com",
            "admin_school",
            school.id,
            roles=["admin_school", "pedagogical_lead"],
        )

        token = _login(client, "updater@test.com")
        assert token is not None

        # Switch to pedagogical_lead
        resp = client.post(
            "/auth/switch-context",
            json={"role": "pedagogical_lead"},
            headers=_auth(token),
        )
        assert resp.status_code == 200

        # Verify database was updated
        db_session.refresh(user)
        assert user.active_context_role == "pedagogical_lead"


# ============================================================
# Tests: ABAC (course_access)
# ============================================================

class TestABACAccess:
    def test_basic_user_cannot_access_golden_course(self, client, db_session):
        """Test that a Basic user cannot access a Golden-tagged course."""
        from app.services.course_access import check_abac_access

        school = _create_school(db_session)
        user = _create_user(
            db_session,
            "basic@test.com",
            "student",
            school.id,
            niveau_scolaire="9eme de base",
        )

        # Create a Basic pack and abonnement
        pack = PackDefinition(
            nom="Basic Pack",
            tier="Basic",
            niveau_scolaire="9eme de base",
            prix_tnd=Decimal("10.00"),
            est_actif=True,
        )
        db_session.add(pack)
        db_session.commit()
        db_session.refresh(pack)

        abonnement = Abonnement(
            user_id=user.id,
            pack_id=pack.id,
            statut="actif",
            debut=datetime.now(timezone.utc),
            fin=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(abonnement)
        db_session.commit()

        # Create a Golden course
        course = Course(
            title="Golden Course",
            school_id=school.id,
            author_id=user.id,
            tag_pack_requis="Golden",
            status=CourseStatus.PUBLISHED,
            is_published=True,
        )
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)

        # Check ABAC access
        result = check_abac_access(user, course, db_session)
        assert result is False

    def test_golden_user_can_access_basic_course(self, client, db_session):
        """Test that a Golden user can access a Basic-tagged course."""
        from app.services.course_access import check_abac_access

        school = _create_school(db_session)
        user = _create_user(
            db_session,
            "golden@test.com",
            "student",
            school.id,
            niveau_scolaire="9eme de base",
        )

        # Create a Golden pack and abonnement
        pack = PackDefinition(
            nom="Golden Pack",
            tier="Golden",
            niveau_scolaire="9eme de base",
            prix_tnd=Decimal("50.00"),
            est_actif=True,
        )
        db_session.add(pack)
        db_session.commit()
        db_session.refresh(pack)

        abonnement = Abonnement(
            user_id=user.id,
            pack_id=pack.id,
            statut="actif",
            debut=datetime.now(timezone.utc),
            fin=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(abonnement)
        db_session.commit()

        # Create a Basic course
        course = Course(
            title="Basic Course",
            school_id=school.id,
            author_id=user.id,
            tag_pack_requis="Basic",
            status=CourseStatus.PUBLISHED,
            is_published=True,
        )
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)

        # Check ABAC access
        result = check_abac_access(user, course, db_session)
        assert result is True

    def test_no_abonnement_denies_access(self, client, db_session):
        """Test that a user without abonnement cannot access a Basic course."""
        from app.services.course_access import check_abac_access

        school = _create_school(db_session)
        user = _create_user(
            db_session,
            "noabon@test.com",
            "student",
            school.id,
            niveau_scolaire="9eme de base",
        )

        # Create a Basic course
        course = Course(
            title="Basic Course",
            school_id=school.id,
            author_id=user.id,
            tag_pack_requis="Basic",
            status=CourseStatus.PUBLISHED,
            is_published=True,
        )
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)

        # Check ABAC access
        result = check_abac_access(user, course, db_session)
        assert result is False


# ============================================================
# Tests: CMS Versioning
# ============================================================

class TestCMSVersioning:
    def test_create_draft_version(self, client, db_session):
        """Test that create-draft-version creates a V2 with is_active_version=False."""
        school = _create_school(db_session)
        teacher = _create_user(
            db_session,
            "teacher@test.com",
            "teacher",
            school.id,
        )

        # Create original course (V1)
        course = Course(
            title="Original Course",
            school_id=school.id,
            author_id=teacher.id,
            version_number=1,
            is_active_version=True,
            status=CourseStatus.PUBLISHED,
            is_published=True,
        )
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)

        token = _login(client, "teacher@test.com")
        assert token is not None

        # Create draft version
        resp = client.post(
            f"/api/courses/{course.id}/create-draft-version",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["version_number"] == 2
        assert "new_course_id" in data

        # Verify V2 exists with is_active_version=False
        v2 = db_session.query(Course).filter(Course.id == data["new_course_id"]).first()
        assert v2 is not None
        assert v2.version_number == 2
        assert v2.is_active_version is False
        assert v2.status == "draft"

        # Verify V1 still has is_active_version=True
        v1 = db_session.query(Course).filter(Course.id == course.id).first()
        assert v1.is_active_version is True

    def test_publish_version_activates_v2(self, client, db_session):
        """Test that publishing V2 deactivates V1."""
        school = _create_school(db_session)
        teacher = _create_user(
            db_session,
            "teacher2@test.com",
            "teacher",
            school.id,
        )

        # Create V1 (active)
        v1 = Course(
            title="Course V1",
            school_id=school.id,
            author_id=teacher.id,
            version_number=1,
            is_active_version=True,
            status=CourseStatus.PUBLISHED,
            is_published=True,
        )
        db_session.add(v1)

        # Create V2 (draft)
        v2 = Course(
            title="Course V1 (V2)",
            school_id=school.id,
            author_id=teacher.id,
            version_number=2,
            is_active_version=False,
            status="draft",
        )
        db_session.add(v2)
        db_session.commit()
        db_session.refresh(v1)
        db_session.refresh(v2)

        token = _login(client, "teacher2@test.com")
        assert token is not None

        # Publish V2
        resp = client.post(
            f"/api/courses/{v2.id}/publish-version",
            headers=_auth(token),
        )
        assert resp.status_code == 200

        # Verify V2 is now active
        db_session.refresh(v2)
        assert v2.is_active_version is True
        assert v2.status == "published"

        # Verify V1 is now inactive
        db_session.refresh(v1)
        assert v1.is_active_version is False

    def test_rollback_to_previous_version(self, client, db_session):
        """Test that rollback deactivates current and reactivates target."""
        school = _create_school(db_session)
        teacher = _create_user(
            db_session,
            "teacher3@test.com",
            "teacher",
            school.id,
        )

        # Create V1 (inactive, was active before)
        v1 = Course(
            title="Course V1",
            school_id=school.id,
            author_id=teacher.id,
            version_number=1,
            is_active_version=False,
            status="archived",
        )
        db_session.add(v1)

        # Create V2 (currently active)
        v2 = Course(
            title="Course V1 (V2)",
            school_id=school.id,
            author_id=teacher.id,
            version_number=2,
            is_active_version=True,
            status=CourseStatus.PUBLISHED,
            is_published=True,
        )
        db_session.add(v2)
        db_session.commit()
        db_session.refresh(v1)
        db_session.refresh(v2)

        token = _login(client, "teacher3@test.com")
        assert token is not None

        # Rollback to V1
        resp = client.post(
            f"/api/courses/{v2.id}/rollback/{v1.id}",
            headers=_auth(token),
        )
        assert resp.status_code == 200

        # Verify V1 is now active
        db_session.refresh(v1)
        assert v1.is_active_version is True
        assert v1.status == "published"

        # Verify V2 is now inactive
        db_session.refresh(v2)
        assert v2.is_active_version is False


# ============================================================
# Tests: Bulk Seats
# ============================================================

class TestBulkSeats:
    def test_purchase_bulk_seats_generates_vouchers(self, client, db_session):
        """Test that purchasing bulk seats generates the correct number of unique vouchers."""
        school = _create_school(db_session)
        admin = _create_user(
            db_session,
            "admin@test.com",
            "admin_school",
            school.id,
        )

        # Create a Teacher Training course
        course = Course(
            title="Teacher Training",
            school_id=school.id,
            author_id=admin.id,
            category_cible="Teacher_Training",
            status=CourseStatus.PUBLISHED,
            is_published=True,
        )
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)

        token = _login(client, "admin@test.com")
        assert token is not None

        # Purchase 5 bulk seats
        resp = client.post(
            "/api/schools/bulk-seats/purchase",
            json={"formation_id": course.id, "quantity": 5},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["vouchers_created"] == 5
        assert len(data["codes"]) == 5

        # Verify all codes are unique
        assert len(set(data["codes"])) == 5

        # Verify vouchers exist in database
        vouchers = db_session.query(BulkSeatVoucher).filter(
            BulkSeatVoucher.school_id == school.id,
        ).all()
        assert len(vouchers) == 5
        assert all(v.status == "unused" for v in vouchers)

    def test_redeem_voucher_enrolls_user(self, client, db_session):
        """Test that redeeming a voucher consumes it and enrolls the user."""
        school = _create_school(db_session)
        admin = _create_user(
            db_session,
            "admin2@test.com",
            "admin_school",
            school.id,
        )

        # Create a Teacher Training course
        course = Course(
            title="Teacher Training 2",
            school_id=school.id,
            author_id=admin.id,
            category_cible="Teacher_Training",
            status=CourseStatus.PUBLISHED,
            is_published=True,
        )
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)

        # Create a voucher
        voucher = BulkSeatVoucher(
            school_id=school.id,
            formation_id=course.id,
            code="TEST-VOUCHER-CODE",
            status="unused",
        )
        db_session.add(voucher)
        db_session.commit()
        db_session.refresh(voucher)

        # Create a student to redeem
        student = _create_user(
            db_session,
            "student_redeem@test.com",
            "student",
            school.id,
        )

        token = _login(client, "student_redeem@test.com")
        assert token is not None

        # Redeem the voucher
        resp = client.post(
            "/api/schools/bulk-seats/redeem",
            json={"code": "TEST-VOUCHER-CODE"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "enrollment_id" in data
        assert data["course_title"] == "Teacher Training 2"

        # Verify voucher is consumed
        db_session.refresh(voucher)
        assert voucher.status == "consumed"
        assert voucher.consumed_by == student.id

        # Verify enrollment exists
        enrollment = db_session.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == student.id,
            CourseEnrollment.course_id == course.id,
        ).first()
        assert enrollment is not None

    def test_redeem_used_voucher_fails(self, client, db_session):
        """Test that redeeming an already consumed voucher returns 400."""
        school = _create_school(db_session)
        admin = _create_user(
            db_session,
            "admin3@test.com",
            "admin_school",
            school.id,
        )

        course = Course(
            title="Teacher Training 3",
            school_id=school.id,
            author_id=admin.id,
            category_cible="Teacher_Training",
            status=CourseStatus.PUBLISHED,
            is_published=True,
        )
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)

        # Create a consumed voucher
        voucher = BulkSeatVoucher(
            school_id=school.id,
            formation_id=course.id,
            code="USED-VOUCHER-CODE",
            status="consumed",
            consumed_by=admin.id,
        )
        db_session.add(voucher)
        db_session.commit()

        student = _create_user(
            db_session,
            "student_fail@test.com",
            "student",
            school.id,
        )

        token = _login(client, "student_fail@test.com")
        assert token is not None

        # Try to redeem used voucher
        resp = client.post(
            "/api/schools/bulk-seats/redeem",
            json={"code": "USED-VOUCHER-CODE"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "déjà été utilisé" in resp.json()["detail"]
