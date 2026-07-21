"""
Tests — Phase 1 : Câblage de has_course_access() sur les endpoints d'accès.
Vérifie qu'un élève SANS pack et SANS inscription reçoit 403 sur un cours payant.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import User, School, Course, Module, Lesson, Quiz, CourseStatus, TransactionType
from app.core.security import get_password_hash

TEST_PASSWORD = "password123"
TEST_HASH = get_password_hash(TEST_PASSWORD)


def _create_user(db, email, role, school_id, niveau_scolaire=None, is_active=True):
    user = User(
        email=email, hashed_password=TEST_HASH, full_name=f"User {email}",
        role=role, is_active=is_active, school_id=school_id,
        niveau_scolaire=niveau_scolaire,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_course(db, school_id, author_id, price=50.0, visibility="public_catalog", status=CourseStatus.PUBLISHED):
    course = Course(
        title="Test Paid Course", slug="test-paid-course",
        school_id=school_id, author_id=author_id,
        price=price, price_dt=price, price_tokens=0,
        visibility=visibility, status=status, is_published=True,
        niveau_scolaire="9eme de base",
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def _create_module(db, course_id):
    module = Module(title="Module 1", course_id=course_id, order=1)
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def _create_lesson(db, module_id, school_id, is_free=False):
    lesson = Lesson(
        title="Lesson 1", module_id=module_id, order=1,
        is_free=is_free, lesson_type="text",
        content_html="<p>Protected content</p>",
        school_id=school_id,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def _create_quiz(db, lesson_id):
    quiz = Quiz(title="Quiz 1", lesson_id=lesson_id, passing_score_percent=50)
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    lesson.quiz_id = quiz.id
    db.commit()
    return quiz


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

    admin = _create_user(db, "admin@test.com", "admin_school", school.id)
    student_no_access = _create_user(db, "student_no@test.com", "student", school.id, niveau_scolaire="9eme de base")
    student_with_enrollment = _create_user(db, "student_enrolled@test.com", "student", school.id, niveau_scolaire="9eme de base")

    course = _create_course(db, school.id, admin.id, price=50.0)
    module = _create_module(db, course.id)
    paid_lesson = _create_lesson(db, module.id, school.id, is_free=False)
    free_lesson = _create_lesson(db, module.id, school.id, is_free=True)
    quiz = _create_quiz(db, paid_lesson.id)

    # Enroll student_with_enrollment (simulates prior purchase)
    from app.models import CourseEnrollment
    enrollment = CourseEnrollment(
        student_id=student_with_enrollment.id,
        course_id=course.id,
        status="active",
    )
    db.add(enrollment)
    db.commit()

    client = TestClient(app)
    tokens = {
        "student_no": _login(client, student_no_access.email),
        "student_enrolled": _login(client, student_with_enrollment.email),
        "admin": _login(client, admin.email),
    }

    yield client, db, {
        "student_no": student_no_access,
        "student_enrolled": student_with_enrollment,
        "admin": admin,
        "course": course,
        "module": module,
        "paid_lesson": paid_lesson,
        "free_lesson": free_lesson,
        "quiz": quiz,
        "school": school,
    }, tokens

    db.close()
    app.dependency_overrides.clear()


class TestLessonAccess:
    def test_no_access_paid_lesson_returns_403(self, setup):
        """Student without enrollment/pack gets 403 on paid lesson content."""
        client, _, data, tokens = setup
        resp = client.get(
            f"/api/learner/lessons/{data['paid_lesson'].id}",
            headers={"Authorization": f"Bearer {tokens['student_no']}"},
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"

    def test_enrolled_student_can_access_paid_lesson(self, setup):
        """Student with active enrollment CAN access paid lesson."""
        client, _, data, tokens = setup
        resp = client.get(
            f"/api/learner/lessons/{data['paid_lesson'].id}",
            headers={"Authorization": f"Bearer {tokens['student_enrolled']}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert resp.json()["title"] == "Lesson 1"

    def test_free_lesson_accessible_to_all(self, setup):
        """Free lessons are accessible even without enrollment."""
        client, _, data, tokens = setup
        resp = client.get(
            f"/api/learner/lessons/{data['free_lesson'].id}",
            headers={"Authorization": f"Bearer {tokens['student_no']}"},
        )
        assert resp.status_code == 200, f"Expected 200 for free lesson, got {resp.status_code}"

    def test_author_can_access_own_lesson(self, setup):
        """Course author can always access their own lessons."""
        client, _, data, tokens = setup
        resp = client.get(
            f"/api/learner/lessons/{data['paid_lesson'].id}",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert resp.status_code == 200, f"Expected 200 for author, got {resp.status_code}"


class TestQuizAccess:
    def test_no_access_paid_quiz_returns_403(self, setup):
        """Student without enrollment gets 403 when starting a paid quiz."""
        client, _, data, tokens = setup
        resp = client.post(
            f"/api/learner/quizzes/{data['quiz'].id}/start",
            headers={"Authorization": f"Bearer {tokens['student_no']}"},
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"

    def test_enrolled_student_can_start_quiz(self, setup):
        """Student with active enrollment CAN start the quiz."""
        client, _, data, tokens = setup
        resp = client.post(
            f"/api/learner/quizzes/{data['quiz'].id}/start",
            headers={"Authorization": f"Bearer {tokens['student_enrolled']}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


class TestSyllabusAccess:
    def test_no_access_syllabus_returns_403(self, setup):
        """Student without enrollment gets 403 on course syllabus."""
        client, _, data, tokens = setup
        resp = client.get(
            f"/api/learner/courses/{data['course'].id}/syllabus",
            headers={"Authorization": f"Bearer {tokens['student_no']}"},
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"

    def test_enrolled_student_can_access_syllabus(self, setup):
        """Student with active enrollment CAN access syllabus."""
        client, _, data, tokens = setup
        resp = client.get(
            f"/api/learner/courses/{data['course'].id}/syllabus",
            headers={"Authorization": f"Bearer {tokens['student_enrolled']}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"


class TestPurchaseCourse:
    def test_purchase_fails_with_insufficient_balance(self, setup):
        """Purchase returns 402 when dt_balance is insufficient."""
        client, db, data, tokens = setup
        # student_no has 0 dt_balance by default
        resp = client.post(
            f"/api/courses/{data['course'].id}/purchase",
            headers={"Authorization": f"Bearer {tokens['student_no']}"},
        )
        assert resp.status_code == 402, f"Expected 402, got {resp.status_code}: {resp.text}"
        # Verify no CoursePurchase was created
        from app.models import CoursePurchase
        count = db.query(CoursePurchase).filter(
            CoursePurchase.student_id == data["student_no"].id,
            CoursePurchase.course_id == data["course"].id,
        ).count()
        assert count == 0, "No purchase should be created on insufficient balance"

    def test_purchase_succeeds_and_deducts_correct_amount(self, setup):
        """Purchase succeeds and deducts exactly the course price from dt_balance."""
        client, db, data, tokens = setup
        # Give student enough balance
        data["student_no"].dt_balance = 100.0
        db.commit()

        resp = client.post(
            f"/api/courses/{data['course'].id}/purchase",
            headers={"Authorization": f"Bearer {tokens['student_no']}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["amount_paid"] == 50.0, f"Expected 50.0 paid, got {body['amount_paid']}"
        assert body["remaining_balance"] == 50.0, f"Expected 50.0 remaining, got {body['remaining_balance']}"

        # Verify dt_balance was actually deducted in DB
        db.refresh(data["student_no"])
        assert data["student_no"].dt_balance == 50.0, f"DB balance should be 50.0, got {data['student_no'].dt_balance}"

        # Verify Transaction was created
        from app.models import Transaction
        tx = db.query(Transaction).filter(
            Transaction.user_id == data["student_no"].id,
            Transaction.type == TransactionType.COURSE_PURCHASE,
        ).first()
        assert tx is not None, "Transaction should be created"
        assert tx.amount == 50.0

        # Verify enrollment was created
        from app.models import CourseEnrollment
        enrollment = db.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == data["student_no"].id,
            CourseEnrollment.course_id == data["course"].id,
        ).first()
        assert enrollment is not None, "Enrollment should be created after purchase"

    def test_purchase_prevents_duplicate(self, setup):
        """Cannot purchase the same course twice."""
        client, db, data, tokens = setup
        data["student_no"].dt_balance = 200.0
        db.commit()

        # First purchase succeeds
        resp1 = client.post(
            f"/api/courses/{data['course'].id}/purchase",
            headers={"Authorization": f"Bearer {tokens['student_no']}"},
        )
        assert resp1.status_code == 200

        # Second purchase fails
        resp2 = client.post(
            f"/api/courses/{data['course'].id}/purchase",
            headers={"Authorization": f"Bearer {tokens['student_no']}"},
        )
        assert resp2.status_code == 400, f"Duplicate purchase should fail, got {resp2.status_code}"
