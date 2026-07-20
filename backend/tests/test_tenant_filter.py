"""
Tests critiques — Filtre multi-tenant ORM (C1).
Vérifie que le filtre automatique school_id isole les données entre écoles.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, current_tenant_id, _tenant_filter_suppressed
from app.models import (
    User, School, Course, CourseStatus,
)


TEST_PASSWORD = "password123"


@pytest.fixture(scope="function")
def db():
    """In-memory test DB with all tables. Yields (session, school_a, school_b, courses)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    # Ensure no tenant filter is active during setup
    current_tenant_id.set(None)
    _tenant_filter_suppressed.set(False)

    # --- Créer deux écoles ---
    school_a = School(name="École A", slug="ecole-a", subscription_tier="free")
    school_b = School(name="École B", slug="ecole-b", subscription_tier="free")
    session.add_all([school_a, school_b])
    session.flush()

    # --- Users par école ---
    admin_a = User(
        email="admin_a@test.com", hashed_password="x", full_name="Admin A",
        role="admin_school", is_active=True, school_id=school_a.id,
    )
    admin_b = User(
        email="admin_b@test.com", hashed_password="x", full_name="Admin B",
        role="admin_school", is_active=True, school_id=school_b.id,
    )
    super_admin = User(
        email="super@test.com", hashed_password="x", full_name="Super Admin",
        role="super_admin", is_active=True, school_id=school_a.id,
    )
    pedagogical_admin = User(
        email="peda@test.com", hashed_password="x", full_name="Peda Admin",
        role="pedagogical_admin", is_active=True, school_id=school_a.id,
    )
    session.add_all([admin_a, admin_b, super_admin, pedagogical_admin])
    session.flush()

    # --- Cours par école ---
    course_a1 = Course(
        title="Maths A1", school_id=school_a.id, author_id=admin_a.id,
        status=CourseStatus.PUBLISHED, is_published=True, price=0,
    )
    course_a2 = Course(
        title="Maths A2", school_id=school_a.id, author_id=admin_a.id,
        status=CourseStatus.DRAFT, is_published=False, price=0,
    )
    course_b1 = Course(
        title="Sciences B1", school_id=school_b.id, author_id=admin_b.id,
        status=CourseStatus.PUBLISHED, is_published=True, price=0,
    )
    session.add_all([course_a1, course_a2, course_b1])
    session.commit()

    yield session, school_a, school_b, admin_a, admin_b, super_admin, pedagogical_admin, course_a1, course_a2, course_b1

    # Cleanup: reset ContextVars after test
    current_tenant_id.set(None)
    _tenant_filter_suppressed.set(False)
    session.close()


class TestTenantFilterSchoolIsolation:
    """Le filtre ORM empêche un admin_school de voir les données d'une autre école."""

    def test_admin_a_sees_only_school_a_courses(self, db):
        """admin_school de l'école A ne voit QUE les cours de l'école A."""
        session, school_a, school_b, admin_a, admin_b, _, _, course_a1, course_a2, course_b1 = db

        # Activer le filtre pour l'école A
        current_tenant_id.set(school_a.id)
        _tenant_filter_suppressed.set(False)

        courses = session.query(Course).all()
        course_ids = {c.id for c in courses}

        # L'admin A ne voit que les cours A
        assert course_a1.id in course_ids, "course_a1 doit être visible"
        assert course_a2.id in course_ids, "course_a2 doit être visible"
        assert course_b1.id not in course_ids, "course_b1 ne doit PAS être visible"

    def test_admin_b_sees_only_school_b_courses(self, db):
        """admin_school de l'école B ne voit QUE les cours de l'école B (symétrie)."""
        session, school_a, school_b, admin_a, admin_b, _, _, course_a1, course_a2, course_b1 = db

        current_tenant_id.set(school_b.id)
        _tenant_filter_suppressed.set(False)

        courses = session.query(Course).all()
        course_ids = {c.id for c in courses}

        assert course_b1.id in course_ids, "course_b1 doit être visible"
        assert course_a1.id not in course_ids, "course_a1 ne doit PAS être visible"
        assert course_a2.id not in course_ids, "course_a2 ne doit PAS être visible"

    def test_admin_a_does_not_see_school_b_users(self, db):
        """Le filtre s'applique aussi aux users — admin A ne voit pas les users de l'école B."""
        session, school_a, school_b, admin_a, admin_b, _, _, _, _, _ = db

        current_tenant_id.set(school_a.id)
        _tenant_filter_suppressed.set(False)

        users = session.query(User).all()
        user_emails = {u.email for u in users}

        assert "admin_a@test.com" in user_emails, "admin_a doit être visible"
        assert "admin_b@test.com" not in user_emails, "admin_b ne doit PAS être visible"

    def test_admin_b_does_not_see_school_a_users(self, db):
        """Le filtre s'applique aussi aux users — admin B ne voit pas les users de l'école A."""
        session, school_a, school_b, admin_a, admin_b, _, _, _, _, _ = db

        current_tenant_id.set(school_b.id)
        _tenant_filter_suppressed.set(False)

        users = session.query(User).all()
        user_emails = {u.email for u in users}

        assert "admin_b@test.com" in user_emails, "admin_b doit être visible"
        assert "admin_a@test.com" not in user_emails, "admin_a ne doit PAS être visible"


class TestTenantFilterSuperAdmin:
    """super_admin bypass le filtre et voit toutes les écoles."""

    def test_super_admin_sees_all_courses(self, db):
        session, school_a, school_b, _, _, super_admin, _, course_a1, course_a2, course_b1 = db

        current_tenant_id.set(None)
        _tenant_filter_suppressed.set(True)

        courses = session.query(Course).all()
        course_ids = {c.id for c in courses}

        assert course_a1.id in course_ids, "super_admin doit voir course_a1"
        assert course_a2.id in course_ids, "super_admin doit voir course_a2"
        assert course_b1.id in course_ids, "super_admin doit voir course_b1"

    def test_super_admin_sees_all_users(self, db):
        session, school_a, school_b, _, _, super_admin, _, _, _, _ = db

        current_tenant_id.set(None)
        _tenant_filter_suppressed.set(True)

        users = session.query(User).all()
        user_emails = {u.email for u in users}

        assert "admin_a@test.com" in user_emails
        assert "admin_b@test.com" in user_emails
        assert "super@test.com" in user_emails


class TestTenantFilterPedagogicalAdmin:
    """pedagogical_admin bypass le filtre et voit toutes les écoles."""

    def test_pedagogical_admin_sees_all_courses(self, db):
        session, school_a, school_b, _, _, _, pedagogical_admin, course_a1, course_a2, course_b1 = db

        current_tenant_id.set(None)
        _tenant_filter_suppressed.set(True)

        courses = session.query(Course).all()
        course_ids = {c.id for c in courses}

        assert course_a1.id in course_ids
        assert course_a2.id in course_ids
        assert course_b1.id in course_ids


class TestTenantFilterNoFilter:
    """Sans tenant_id défini, le filtre ne s'applique pas (contexte non-authentifié)."""

    def test_no_tenant_sees_all(self, db):
        session, school_a, school_b, _, _, _, _, course_a1, course_a2, course_b1 = db

        current_tenant_id.set(None)
        _tenant_filter_suppressed.set(False)

        courses = session.query(Course).all()
        assert len(courses) == 3, "Sans filtre, tous les cours sont visibles"
