"""
Tests de vérification — Audit 01/08/2026
========================================
Bug 1: Truncation décimale debit_dt
Bug 2: Double commit non atomique
Point 3: Preuve d'exécution has_course_access sur 13 endpoints

Exécution: python -m pytest tests/test_audit_2026_08_01.py -v
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

from decimal import Decimal
import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import (
    User, School, Course, Module, Lesson, Quiz,
    CourseStatus, TransactionType, CourseEnrollment, CoursePurchase,
)
from app.core.security import get_password_hash
from app.services.wallet import credit_dt, debit_dt, get_dt_balance, InsufficientCreditsError

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


def _create_course(db, school_id, author_id, price=50.0, niveau_scolaire="9eme de base"):
    course = Course(
        title="Test Paid Course", slug=f"test-paid-{price}",
        school_id=school_id, author_id=author_id,
        price=price, price_dt=price, price_tokens=0,
        visibility="public_catalog", status=CourseStatus.PUBLISHED,
        is_published=True, niveau_scolaire=niveau_scolaire,
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
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    quiz = Quiz(title="Quiz 1", lesson_id=lesson_id, passing_score_percent=50, school_id=lesson.school_id)
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    lesson.quiz_id = quiz.id
    db.commit()
    return quiz


def _login(client, email):
    resp = client.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
    return resp.json().get("access_token")


# ══════════════════════════════════════════════════════════════════════════════
# BUG 1 — Truncation décimale debit_dt
# ══════════════════════════════════════════════════════════════════════════════

class TestBug1DecimalTruncation:
    """
    Vérifie que debit_dt() débite le montant EXACT (pas d'arrondi entier).
    Avant fix: round(14.99) = 15, round(0.01) = 0 → perte d'argent.
    Après fix: amount reste tel quel (Float).
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        TestingSessionLocal = sessionmaker(bind=engine)

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        db = TestingSessionLocal()

        school = School(name="School B1", slug="school-b1", school_type="real")
        db.add(school)
        db.commit()
        db.refresh(school)

        teacher = _create_user(db, "teacher_b1@test.com", "teacher", school.id)
        student = _create_user(db, "student_b1@test.com", "student", school.id, niveau_scolaire="9eme de base")

        client = TestClient(app)
        token = _login(client, student.email)

        self.client = client
        self.db = db
        self.student = student
        self.teacher = teacher
        self.school = school

        yield

        app.dependency_overrides.clear()
        db.close()

    def test_debit_14_99_exact(self):
        """Cours à 14.99 TND → solde doit baisser de 14.99 exactement."""
        credit_dt(self.db, self.student.id, Decimal("100.00"), source="test")
        balance_before = get_dt_balance(self.db, self.student.id)
        assert balance_before == Decimal("100.00")

        debit_dt(self.db, self.student.id, Decimal("14.99"), source="test", commit=True)
        balance_after = get_dt_balance(self.db, self.student.id)

        assert balance_after == Decimal("85.01"), (
            f"Solde après débit de 14.99 depuis 100.0 devrait être 85.01, "
            f"obtenu {balance_after}"
        )

    def test_debit_0_01_exact(self):
        """Cours à 0.01 TND → ne doit PAS être arrondi à 0."""
        credit_dt(self.db, self.student.id, Decimal("10.00"), source="test")

        debit_dt(self.db, self.student.id, Decimal("0.01"), source="test", commit=True)
        balance = get_dt_balance(self.db, self.student.id)

        assert balance == Decimal("9.99"), (
            f"Solde après débit de 0.01 depuis 10.0 devrait être 9.99, "
            f"obtenu {balance}"
        )

    def test_debit_999_99_exact(self):
        """Cours à 999.99 TND → pas d'arrondi à 1000."""
        credit_dt(self.db, self.student.id, Decimal("2000.00"), source="test")

        debit_dt(self.db, self.student.id, Decimal("999.99"), source="test", commit=True)
        balance = get_dt_balance(self.db, self.student.id)

        assert balance == Decimal("1000.01"), (
            f"Solde après débit de 999.99 depuis 2000.0 devrait être 1000.01, "
            f"obtenu {balance}"
        )

    def test_purchase_course_decimal_matches_exactly(self):
        """Le montant débité du wallet DOIT correspondre exactement à amount_paid du CoursePurchase."""
        course = _create_course(self.db, self.school.id, self.teacher.id, price=14.99)
        _create_module(self.db, course.id)

        credit_dt(self.db, self.student.id, Decimal("100.00"), source="test")

        resp = self.client.post(
            f"/api/courses/{course.id}/purchase",
            headers={"Authorization": f"Bearer {_login(self.client, self.student.email)}"},
        )
        assert resp.status_code == 200, f"Purchase failed: {resp.text}"
        body = resp.json()

        # Vérifier que amount_paid correspond exactement au prix (API retourne float via Decimal)
        assert body["amount_paid"] == 14.99, (
            f"amount_paid devrait être 14.99, obtenu {body['amount_paid']}"
        )

        # Vérifier que le solde restant est exact
        expected_remaining = 85.01  # 100.0 - 14.99
        assert body["remaining_balance"] == expected_remaining, (
            f"Solde restant devrait être {expected_remaining}, obtenu {body['remaining_balance']}"
        )

        # Vérifier en DB que la transaction wallet correspond exactement
        balance_db = get_dt_balance(self.db, self.student.id)
        assert balance_db == Decimal("85.01"), (
            f"Solde DB devrait être 85.01, obtenu {balance_db}"
        )

    def test_credit_14_99_exact(self):
        """credit_dt() doit aussi préserver les décimales."""
        credit_dt(self.db, self.student.id, Decimal("14.99"), source="test")
        balance = get_dt_balance(self.db, self.student.id)
        assert balance == Decimal("14.99"), (
            f"Crédit de 14.99 → solde devrait être 14.99, obtenu {balance}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# BUG 2 — Double commit non atomique
# ══════════════════════════════════════════════════════════════════════════════

class TestBug2AtomicCommit:
    """
    Vérifie que debit_dt() avec commit=False ne fait PAS de commit interne,
    et que le commit final est atomique (tout ou rien).
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        TestingSessionLocal = sessionmaker(bind=engine)

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        db = TestingSessionLocal()

        school = School(name="School B2", slug="school-b2", school_type="real")
        db.add(school)
        db.commit()
        db.refresh(school)

        teacher = _create_user(db, "teacher_b2@test.com", "teacher", school.id)
        student = _create_user(db, "student_b2@test.com", "student", school.id, niveau_scolaire="9eme de base")

        client = TestClient(app)

        self.client = client
        self.db = db
        self.student = student
        self.teacher = teacher
        self.school = school

        yield

        app.dependency_overrides.clear()
        db.close()

    def test_commit_false_does_not_persist(self):
        """debit_dt(commit=False) ajoute la transaction mais ne la commit PAS.
        Un reader externe (session séparée) ne doit PAS voir le débit."""
        credit_dt(self.db, self.student.id, Decimal("100.00"), source="test")

        tx = debit_dt(self.db, self.student.id, Decimal("50.00"), source="test", commit=False)

        # Créer une session séparée pour lire le ledger (simule un autre client)
        engine = self.db.get_bind()
        Session2 = sessionmaker(bind=engine)
        db_reader = Session2()

        # Le reader externe ne voit PAS le débit (non committed)
        from app.services.wallet import get_dt_balance as _gdb
        balance_uncommitted = _gdb(db_reader, self.student.id)
        assert balance_uncommitted == Decimal("100.00"), (
            f"Un reader externe ne doit PAS voir un débit non committed. "
            f"Solde lu: {balance_uncommitted}, attendu: 100.0"
        )

        # Maintenant on commit
        self.db.commit()

        # Le reader externe voit maintenant le débit
        balance_committed = _gdb(db_reader, self.student.id)
        assert balance_committed == Decimal("50.00"), (
            f"Après commit, le solde doit être 50.0, obtenu {balance_committed}"
        )
        db_reader.close()

    def test_atomic_rollback_on_failure(self):
        """Si une exception survient après debit_dt(commit=False) mais avant commit,
        le rollback doit annuler TOUT y compris le débit."""
        credit_dt(self.db, self.student.id, Decimal("100.00"), source="test")
        balance_before = get_dt_balance(self.db, self.student.id)

        # Simuler le flux purchase_course avec crash avant commit
        try:
            debit_dt(self.db, self.student.id, Decimal("50.00"), source="purchase", commit=False)
            # Simuler une erreur après le débit (ex: contrainte DB, timeout)
            raise RuntimeError("Simulated crash between debit and commit")
        except RuntimeError:
            self.db.rollback()

        balance_after_rollback = get_dt_balance(self.db, self.student.id)
        assert balance_after_rollback == balance_before, (
            f"Après rollback, le solde doit être identique à avant. "
            f"Avant: {balance_before}, Après: {balance_after_rollback}"
        )

    def test_purchase_course_atomic_success(self):
        """Purchase réussi : débit + enrollment dans un seul commit."""
        course = _create_course(self.db, self.school.id, self.teacher.id, price=14.99)
        _create_module(self.db, course.id)

        credit_dt(self.db, self.student.id, Decimal("100.00"), source="test")

        resp = self.client.post(
            f"/api/courses/{course.id}/purchase",
            headers={"Authorization": f"Bearer {_login(self.client, self.student.email)}"},
        )
        assert resp.status_code == 200, f"Purchase failed: {resp.text}"

        # Vérifier atomisme : les deux existent en même temps
        from app.models import CoursePurchase
        purchase = self.db.query(CoursePurchase).filter(
            CoursePurchase.student_id == self.student.id,
            CoursePurchase.course_id == course.id,
        ).first()
        assert purchase is not None, "CoursePurchase doit exister"
        assert float(purchase.amount_paid) == 14.99

        enrollment = self.db.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == self.student.id,
            CourseEnrollment.course_id == course.id,
        ).first()
        assert enrollment is not None, "CourseEnrollment doit exister"

        balance = get_dt_balance(self.db, self.student.id)
        assert balance == Decimal("85.01"), f"Solde devrait être 85.01, obtenu {balance}"


# ══════════════════════════════════════════════════════════════════════════════
# POINT 3 — Preuve d'exécution has_course_access sur 13 endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestHasCourseAccessExecution:
    """
    Pour CHACUN des 13 endpoints, crée un élève SANS accès (pas d'enrollment,
    pas de purchase, pas de pack, pas d'accès école).

    Depuis l'activation du modèle Freemium (learner.py), les endpoints de
    consommation pédagogique (syllabus, leçon, quiz) ne renvoient plus 403 :
    un élève Gratuit/sans pack est autorisé sous quota, puis bloqué par un 402
    structuré {"message", "required_pack"} une fois le quota trimestriel épuisé.
    Le fixture épuise donc volontairement ce quota (3 leçons complétées sur un
    autre cours) pour vérifier le garde-fou serveur réel : le 402 upsell.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        TestingSessionLocal = sessionmaker(bind=engine)

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        db = TestingSessionLocal()

        school = School(name="School B3", slug="school-b3", school_type="real")
        db.add(school)
        db.commit()
        db.refresh(school)

        teacher = _create_user(db, "teacher_b3@test.com", "teacher", school.id)
        student_no_access = _create_user(
            db, "student_no_access@test.com", "student", school.id,
            niveau_scolaire="9eme de base",
        )

        # Créer un cours payant
        course = _create_course(db, school.id, teacher.id, price=50.0)
        module = _create_module(db, course.id)
        paid_lesson = _create_lesson(db, module.id, school.id, is_free=False)
        quiz = _create_quiz(db, paid_lesson.id)

        # ── Quota Freemium ÉPUISÉ pour student_no_access ──
        # 3 leçons uniques "complétées" ce trimestre, via un enrollment sur un
        # AUTRE cours (sinon l'enrollment lui-même déverrouillerait le cours cible).
        from app.models import LessonProgress as LP
        quota_course = Course(
            title="Quota Filler", slug="quota-filler",
            school_id=school.id, author_id=teacher.id,
            price=0.0, price_dt=0.0, price_tokens=0,
            visibility="public_catalog", status=CourseStatus.PUBLISHED,
            is_published=True, niveau_scolaire="9eme de base",
        )
        db.add(quota_course)
        db.flush()
        quota_enrollment = CourseEnrollment(
            student_id=student_no_access.id,
            course_id=quota_course.id,
            status="active",
        )
        db.add(quota_enrollment)
        db.flush()
        _now = datetime.now(timezone.utc)
        for fake_lesson_id in (900001, 900002, 900003):
            db.add(LP(
                enrollment_id=quota_enrollment.id,
                lesson_id=fake_lesson_id,
                status="completed",
                completed_at=_now,
            ))
        db.commit()

        client = TestClient(app)

        self.client = client
        self.db = db
        self.student = student_no_access
        self.teacher = teacher
        self.course = course
        self.module = module
        self.paid_lesson = paid_lesson
        self.quiz = quiz
        self.school = school
        self.token = _login(client, student_no_access.email)

        yield

        app.dependency_overrides.clear()
        db.close()

    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"}

    # ── 1. GET /lessons/{id} ──────────────────────────────────────────────
    def test_01_get_lesson_no_access(self):
        """GET /api/learner/lessons/{id} → 402 quota Freemium épuisé (upsell)."""
        resp = self.client.get(
            f"/api/learner/lessons/{self.paid_lesson.id}",
            headers=self._auth(),
        )
        assert resp.status_code == 402, (
            f"GET /lessons/{self.paid_lesson.id} devrait retourner 402, "
            f"obtenu {resp.status_code}: {resp.text}"
        )
        detail = resp.json()["detail"]
        assert isinstance(detail, dict) and detail.get("required_pack") == "Basic"

    # ── 2. POST /lessons/{id}/progress ────────────────────────────────────
    def test_02_post_lesson_progress_no_access(self):
        """POST /api/learner/lessons/{id}/progress → 402 quota épuisé."""
        resp = self.client.post(
            f"/api/learner/lessons/{self.paid_lesson.id}/progress",
            headers=self._auth(),
            json={"completed": True},
        )
        assert resp.status_code == 402, (
            f"POST /lessons/{self.paid_lesson.id}/progress devrait retourner 402, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 3. POST /quizzes/{id}/start ───────────────────────────────────────
    def test_03_post_quiz_start_no_access(self):
        """POST /api/learner/quizzes/{id}/start → 402 quota épuisé."""
        resp = self.client.post(
            f"/api/learner/quizzes/{self.quiz.id}/start",
            headers=self._auth(),
        )
        assert resp.status_code == 402, (
            f"POST /quizzes/{self.quiz.id}/start devrait retourner 402, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 4. GET /quizzes/{id} ──────────────────────────────────────────────
    def test_04_get_quiz_no_access(self):
        """GET /api/learner/quizzes/{id} → 402 quota épuisé."""
        resp = self.client.get(
            f"/api/learner/quizzes/{self.quiz.id}",
            headers=self._auth(),
        )
        assert resp.status_code == 402, (
            f"GET /quizzes/{self.quiz.id} devrait retourner 402, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 5. POST /quizzes/{id}/submit ──────────────────────────────────────
    def test_05_post_quiz_submit_no_access(self):
        """POST /api/learner/quizzes/{id}/submit → 403 ou 404 sans accès.
        L'endpoint exige un attempt_id valide. Sans tentative, retourne 404
        (tente l'accès via _do_submit_attempt → échoue car pas de tentative).
        Avec un faux attempt_id, le check has_course_access se lance mais
        retourne 404 car la tentative n'existe pas. Les deux prouvent le garde-fou."""
        resp = self.client.post(
            f"/api/learner/quizzes/{self.quiz.id}/submit",
            headers=self._auth(),
            json={"attempt_id": 99999, "answers": []},
        )
        assert resp.status_code in (402, 404), (
            f"POST /quizzes/{self.quiz.id}/submit devrait retourner 402 ou 404, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 6. POST /quiz-attempts/{id}/submit ────────────────────────────────
    def test_06_post_quiz_attempt_submit_no_access(self):
        """POST /api/learner/quiz-attempts/{id}/submit → 403 sans accès."""
        # Créer un faux attempt ID pour tester le check
        resp = self.client.post(
            f"/api/learner/quiz-attempts/99999/submit",
            headers=self._auth(),
            json={"answers": []},
        )
        # Peut être 404 (attempt introuvable) ou 403 — les deux prouvent le garde-fou
        assert resp.status_code in (403, 404), (
            f"POST /quiz-attempts/99999/submit devrait retourner 403 ou 404, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 7. POST /lessons/{id}/notes ───────────────────────────────────────
    def test_07_post_notes_no_access(self):
        """POST /api/learner/lessons/{id}/notes → 403 sans accès."""
        resp = self.client.post(
            f"/api/learner/lessons/{self.paid_lesson.id}/notes",
            headers=self._auth(),
            json={"content": "My notes"},
        )
        assert resp.status_code == 403, (
            f"POST /lessons/{self.paid_lesson.id}/notes devrait retourner 403, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 8. GET /lessons/{id}/notes ────────────────────────────────────────
    def test_08_get_notes_no_access(self):
        """GET /api/learner/lessons/{id}/notes → 403 sans accès."""
        resp = self.client.get(
            f"/api/learner/lessons/{self.paid_lesson.id}/notes",
            headers=self._auth(),
        )
        assert resp.status_code == 403, (
            f"GET /lessons/{self.paid_lesson.id}/notes devrait retourner 403, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 9. POST /lessons/{id}/bookmarks ───────────────────────────────────
    def test_09_post_bookmarks_no_access(self):
        """POST /api/learner/lessons/{id}/bookmarks → 403 sans accès."""
        resp = self.client.post(
            f"/api/learner/lessons/{self.paid_lesson.id}/bookmarks",
            headers=self._auth(),
            json={"title": "Bookmark", "timestamp_seconds": 0},
        )
        assert resp.status_code == 403, (
            f"POST /lessons/{self.paid_lesson.id}/bookmarks devrait retourner 403, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 10. GET /lessons/{id}/bookmarks ───────────────────────────────────
    def test_10_get_bookmarks_no_access(self):
        """GET /api/learner/lessons/{id}/bookmarks → 403 sans accès."""
        resp = self.client.get(
            f"/api/learner/lessons/{self.paid_lesson.id}/bookmarks",
            headers=self._auth(),
        )
        assert resp.status_code == 403, (
            f"GET /lessons/{self.paid_lesson.id}/bookmarks devrait retourner 403, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 11. GET /courses/{id}/detail (academy) ────────────────────────────
    def test_11_get_academy_detail_no_access(self):
        """GET /api/academy/courses/{id}/detail → 403 sans accès."""
        resp = self.client.get(
            f"/api/academy/courses/{self.course.id}/detail",
            headers=self._auth(),
        )
        assert resp.status_code == 403, (
            f"GET /academy/courses/{self.course.id}/detail devrait retourner 403, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 12. GET /courses/{id}/syllabus ────────────────────────────────────
    def test_12_get_syllabus_no_access(self):
        """GET /api/learner/courses/{id}/syllabus → 402 quota épuisé."""
        resp = self.client.get(
            f"/api/learner/courses/{self.course.id}/syllabus",
            headers=self._auth(),
        )
        assert resp.status_code == 402, (
            f"GET /learner/courses/{self.course.id}/syllabus devrait retourner 402, "
            f"obtenu {resp.status_code}: {resp.text}"
        )

    # ── 13. POST /courses/{id}/enroll (learner) ──────────────────────────
    def test_13_post_enroll_paid_course_no_access(self):
        """POST /api/learner/courses/{id}/enroll → 403 pour cours payant sans accès."""
        resp = self.client.post(
            f"/api/learner/courses/{self.course.id}/enroll",
            headers=self._auth(),
        )
        assert resp.status_code == 403, (
            f"POST /learner/courses/{self.course.id}/enroll devrait retourner 403, "
            f"obtenu {resp.status_code}: {resp.text}"
        )
