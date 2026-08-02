"""
Tenant isolation tests — verifies School A cannot access School B resources.

Covers:
1. courses.py: update_course / list_enrollments blocked for cross-school
2. lms.py: delete_enrollment blocked for cross-school
3. academy.py: list_quiz_attempts / get_quiz blocked for cross-school
4. adaptive_pathway.py: /notions/{id}/statut-publication returns 403 for student

Both 403 (explicit deny) and 404 (tenant filter hides resource) are acceptable.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    User, School, Course, Module, Lesson,
    ClassRoom, ClassroomEnrollment,
    Quiz,
    NiveauEtude, Matiere, ChapterPathway, Notion, ContenuNotion,
)
from app.core.security import get_password_hash

from tests.conftest import TEST_PASSWORD, TEST_HASH, _login, _auth


@pytest.fixture(scope="function")
def test_db(_base_session):
    """Two schools. Teacher A is author of course B (cross-school ownership trap)."""
    db = _base_session

    # Ensure pending_validation column exists (added to School model)
    try:
        db.execute(text("ALTER TABLE schools ADD COLUMN pending_validation BOOLEAN DEFAULT 0"))
    except Exception:
        pass  # column already exists

    school_a = School(name="School A", slug="school-a", subscription_tier="free")
    db.add(school_a)
    db.commit()
    db.refresh(school_a)

    teacher_a = User(
        email="teacher_a@test.com", hashed_password=TEST_HASH,
        full_name="Teacher A", role="teacher", is_active=True,
        is_approved=True, school_id=school_a.id,
    )
    db.add(teacher_a)
    db.commit()
    db.refresh(teacher_a)

    student_a = User(
        email="student_a@test.com", hashed_password=TEST_HASH,
        full_name="Student A", role="student", is_active=True,
        is_approved=True, school_id=school_a.id,
    )
    db.add(student_a)
    db.commit()
    db.refresh(student_a)

    course_a = Course(
        school_id=school_a.id, author_id=teacher_a.id,
        title="Course A", status="published", is_published=True,
        owner_type="school", price=0,
    )
    db.add(course_a)
    db.commit()
    db.refresh(course_a)

    class_a = ClassRoom(
        name="Class A", school_id=school_a.id, teacher_id=teacher_a.id,
        invite_code="classA",
    )
    db.add(class_a)
    db.commit()
    db.refresh(class_a)

    enrollment_a = ClassroomEnrollment(classroom_id=class_a.id, student_id=student_a.id)
    db.add(enrollment_a)
    db.commit()
    db.refresh(enrollment_a)

    school_b = School(name="School B", slug="school-b", subscription_tier="free")
    db.add(school_b)
    db.commit()
    db.refresh(school_b)

    teacher_b = User(
        email="teacher_b@test.com", hashed_password=TEST_HASH,
        full_name="Teacher B", role="teacher", is_active=True,
        is_approved=True, school_id=school_b.id,
    )
    db.add(teacher_b)
    db.commit()
    db.refresh(teacher_b)

    course_b = Course(
        school_id=school_b.id, author_id=teacher_a.id,
        title="Course B (School B)", status="published", is_published=True,
        owner_type="school", price=0,
    )
    db.add(course_b)
    db.commit()
    db.refresh(course_b)

    module_b = Module(course_id=course_b.id, title="Module B", order=0)
    db.add(module_b)
    db.commit()
    db.refresh(module_b)

    lesson_b = Lesson(
        module_id=module_b.id, title="Lesson B", order=0,
        school_id=school_b.id,
    )
    db.add(lesson_b)
    db.commit()
    db.refresh(lesson_b)

    quiz_b = Quiz(title="Quiz B", lesson_id=lesson_b.id, school_id=school_b.id)
    db.add(quiz_b)
    db.commit()
    db.refresh(quiz_b)

    class_b = ClassRoom(
        name="Class B", school_id=school_b.id, teacher_id=teacher_b.id,
        invite_code="classB",
    )
    db.add(class_b)
    db.commit()
    db.refresh(class_b)

    enrollment_b = ClassroomEnrollment(classroom_id=class_b.id, student_id=student_a.id)
    db.add(enrollment_b)
    db.commit()
    db.refresh(enrollment_b)

    niveau = NiveauEtude(nom="9ème de base", ordre=9)
    db.add(niveau)
    db.commit()
    db.refresh(niveau)

    matiere = Matiere(niveau_etude_id=niveau.id, nom="Mathématiques")
    db.add(matiere)
    db.commit()
    db.refresh(matiere)

    chapitre = ChapterPathway(matiere_id=matiere.id, nom="Chapitre 1", ordre=1)
    db.add(chapitre)
    db.commit()
    db.refresh(chapitre)

    notion_a = Notion(chapitre_id=chapitre.id, nom="Notion A", ordre=1)
    db.add(notion_a)
    db.commit()
    db.refresh(notion_a)

    contenu_a = ContenuNotion(
        notion_id=notion_a.id, niveau_assimilation="standard",
        type_ressource="cours", contenu="Contenu A",
        enseignant_id=teacher_a.id, statut_pedagogique="a",
    )
    db.add(contenu_a)
    db.commit()

    yield (
        db,
        school_a, teacher_a, student_a, course_a, class_a, enrollment_a, quiz_b,
        school_b, teacher_b, course_b, class_b, enrollment_b, notion_a,
    )


@pytest.fixture(scope="function")
def client(test_db):
    return TestClient(app)


class TestCoursesTenantIsolation:
    """courses.py: Teacher A authored course B but it belongs to school B."""

    def test_update_course_cross_school_returns_403_or_404(self, client, test_db):
        (
            db, school_a, teacher_a, student_a, course_a, class_a, enrollment_a, quiz_b,
            school_b, teacher_b, course_b, class_b, enrollment_b, notion_a,
        ) = test_db

        token_a = _login(client, "teacher_a@test.com")
        assert token_a, "Teacher A login failed"

        resp = client.put(
            f"/courses/{course_b.id}",
            json={"title": "Hacked Title"},
            headers=_auth(token_a),
        )
        assert resp.status_code in (403, 404), (
            f"Expected 403 or 404 for cross-school update, got {resp.status_code}: {resp.text}"
        )

    def test_list_enrollments_cross_school_returns_403_or_404(self, client, test_db):
        (
            db, school_a, teacher_a, student_a, course_a, class_a, enrollment_a, quiz_b,
            school_b, teacher_b, course_b, class_b, enrollment_b, notion_a,
        ) = test_db

        token_a = _login(client, "teacher_a@test.com")

        resp = client.get(
            f"/courses/{course_b.id}/enrollments",
            headers=_auth(token_a),
        )
        assert resp.status_code in (403, 404), (
            f"Expected 403 or 404 for cross-school enrollments, got {resp.status_code}: {resp.text}"
        )


class TestLmsTenantIsolation:
    """lms.py: Teacher A cannot delete enrollment from School B class."""

    def test_delete_enrollment_cross_school_returns_403(self, client, test_db):
        (
            db, school_a, teacher_a, student_a, course_a, class_a, enrollment_a, quiz_b,
            school_b, teacher_b, course_b, class_b, enrollment_b, notion_a,
        ) = test_db

        token_a = _login(client, "teacher_a@test.com")
        assert token_a, "Teacher A login failed"

        resp = client.delete(
            f"/enrollments/{enrollment_b.id}",
            headers=_auth(token_a),
        )
        assert resp.status_code in (403, 404), (
            f"Expected 403 or 404 for cross-school enrollment delete, got {resp.status_code}: {resp.text}"
        )


class TestAcademyTenantIsolation:
    """academy.py: Teacher A cannot access School B quiz attempts."""

    def test_list_quiz_attempts_cross_school_returns_403_or_404(self, client, test_db):
        (
            db, school_a, teacher_a, student_a, course_a, class_a, enrollment_a, quiz_b,
            school_b, teacher_b, course_b, class_b, enrollment_b, notion_a,
        ) = test_db

        token_a = _login(client, "teacher_a@test.com")
        assert token_a, "Teacher A login failed"

        resp = client.get(
            f"/quizzes/{quiz_b.id}/attempts",
            headers=_auth(token_a),
        )
        assert resp.status_code in (403, 404), (
            f"Expected 403 or 404 for cross-school quiz attempts, got {resp.status_code}: {resp.text}"
        )

    def test_get_quiz_cross_school_returns_403_or_404(self, client, test_db):
        (
            db, school_a, teacher_a, student_a, course_a, class_a, enrollment_a, quiz_b,
            school_b, teacher_b, course_b, class_b, enrollment_b, notion_a,
        ) = test_db

        token_a = _login(client, "teacher_a@test.com")

        resp = client.get(
            f"/quizzes/{quiz_b.id}",
            headers=_auth(token_a),
        )
        assert resp.status_code in (403, 404), (
            f"Expected 403 or 404 for cross-school quiz, got {resp.status_code}: {resp.text}"
        )


class TestAdaptivePathwayTenantIsolation:
    """adaptive_pathway.py: Students cannot access /notions/{id}/statut-publication."""

    def test_student_statut_publication_returns_403(self, client, test_db):
        (
            db, school_a, teacher_a, student_a, course_a, class_a, enrollment_a, quiz_b,
            school_b, teacher_b, course_b, class_b, enrollment_b, notion_a,
        ) = test_db

        token_student = _login(client, "student_a@test.com")
        assert token_student, "Student A login failed"

        resp = client.get(
            f"/api/pathway/notions/{notion_a.id}/statut-publication",
            headers=_auth(token_student),
        )
        assert resp.status_code in (403, 404), (
            f"Expected 403 or 404 for student accessing statut-publication, got {resp.status_code}: {resp.text}"
        )

    def test_teacher_statut_publication_returns_200(self, client, test_db):
        (
            db, school_a, teacher_a, student_a, course_a, class_a, enrollment_a, quiz_b,
            school_b, teacher_b, course_b, class_b, enrollment_b, notion_a,
        ) = test_db

        token_teacher = _login(client, "teacher_a@test.com")
        assert token_teacher, "Teacher A login failed"

        resp = client.get(
            f"/api/pathway/notions/{notion_a.id}/statut-publication",
            headers=_auth(token_teacher),
        )
        assert resp.status_code == 200, (
            f"Expected 200 for teacher accessing statut-publication, got {resp.status_code}: {resp.text}"
        )


# ---------------------------------------------------------------------------
# SECURITY: Admin-school cross-school isolation tests
# ---------------------------------------------------------------------------

class TestAdminSchoolTenantIsolation:
    """Verify admin_school from School A gets 403 when accessing School B resources.

    These tests enforce the security requirement that school admins can only
    manage their own school's data.
    """

    @pytest.fixture(scope="function")
    def admin_setup(self, _base_session):
        """Two schools with admin_school users in each."""
        db = _base_session

        # Ensure pending_validation column exists
        try:
            db.execute(text("ALTER TABLE schools ADD COLUMN pending_validation BOOLEAN DEFAULT 0"))
        except Exception:
            pass

        school_a = School(name="Admin School A", slug="admin-school-a", subscription_tier="free")
        db.add(school_a)
        db.commit()
        db.refresh(school_a)

        admin_a = User(
            email="admin_a@test.com", hashed_password=TEST_HASH,
            full_name="Admin A", role="admin_school", is_active=True,
            is_approved=True, school_id=school_a.id,
        )
        db.add(admin_a)
        db.commit()
        db.refresh(admin_a)

        course_a = Course(
            school_id=school_a.id, author_id=admin_a.id,
            title="Course A", status="published", is_published=True,
            owner_type="school", price=0,
        )
        db.add(course_a)
        db.commit()
        db.refresh(course_a)

        school_b = School(name="Admin School B", slug="admin-school-b", subscription_tier="free")
        db.add(school_b)
        db.commit()
        db.refresh(school_b)

        admin_b = User(
            email="admin_b@test.com", hashed_password=TEST_HASH,
            full_name="Admin B", role="admin_school", is_active=True,
            is_approved=True, school_id=school_b.id,
        )
        db.add(admin_b)
        db.commit()
        db.refresh(admin_b)

        course_b = Course(
            school_id=school_b.id, author_id=admin_b.id,
            title="Course B", status="published", is_published=True,
            owner_type="school", price=0,
        )
        db.add(course_b)
        db.commit()
        db.refresh(course_b)

        student_b = User(
            email="student_b_admin@test.com", hashed_password=TEST_HASH,
            full_name="Student B", role="student", is_active=True,
            is_approved=True, school_id=school_b.id,
        )
        db.add(student_b)
        db.commit()
        db.refresh(student_b)

        yield db, school_a, admin_a, course_a, school_b, admin_b, course_b, student_b

    @pytest.fixture(scope="function")
    def admin_client(self, admin_setup):
        return TestClient(app)

    def test_admin_school_cannot_list_cross_school_courses(self, admin_client, admin_setup):
        """admin_school A tries to list courses of school B → 403 or 404."""
        (
            db, school_a, admin_a, course_a,
            school_b, admin_b, course_b, student_b,
        ) = admin_setup

        token_a = _login(admin_client, "admin_a@test.com")
        assert token_a, "Admin A login failed"

        # academy.py list_courses filters by school_id via ORM tenant filter,
        # so admin A should see 0 courses (empty list) or 403 if explicit check fires.
        resp = admin_client.get(
            "/api/courses",
            headers=_auth(token_a),
        )
        # With tenant filter, admin_a only sees school_a courses — course_b is hidden.
        assert resp.status_code == 200
        data = resp.json()
        course_ids = [c["id"] for c in data.get("items", [])]
        assert course_b.id not in course_ids, (
            f"Cross-school course {course_b.id} leaked to admin A!"
        )

    def test_admin_school_cannot_update_cross_school_course(self, admin_client, admin_setup):
        """admin_school A tries to update course B → 403 or 404."""
        (
            db, school_a, admin_a, course_a,
            school_b, admin_b, course_b, student_b,
        ) = admin_setup

        token_a = _login(admin_client, "admin_a@test.com")
        assert token_a, "Admin A login failed"

        resp = admin_client.put(
            f"/courses/{course_b.id}",
            json={"title": "Hacked Title"},
            headers=_auth(token_a),
        )
        assert resp.status_code in (403, 404), (
            f"Expected 403 or 404 for cross-school update, got {resp.status_code}: {resp.text}"
        )

    def test_admin_school_cannot_access_cross_school_students(self, admin_client, admin_setup):
        """admin_school A tries to list users (students) of school B → only sees school A users."""
        (
            db, school_a, admin_a, course_a,
            school_b, admin_b, course_b, student_b,
        ) = admin_setup

        token_a = _login(admin_client, "admin_a@test.com")
        assert token_a, "Admin A login failed"

        resp = admin_client.get(
            "/api/admin/users",
            headers=_auth(token_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        user_ids = [u["id"] for u in data.get("items", [])]
        assert student_b.id not in user_ids, (
            f"Cross-school student {student_b.id} leaked to admin A!"
        )
