"""
Phase 1.2 — IDOR on student scores fix.

Test 1 (RED → GREEN): student A must NOT be able to submit a score for student B.
Test 2 (GREEN): student can submit a score for themselves.
Test 3 (GREEN): teacher can submit a score for any student.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.models import User, School, NiveauEtude, Matiere, ChapterPathway
from app.core.security import get_password_hash

from tests.conftest import TEST_PASSWORD, TEST_HASH, _login, _auth


@pytest.fixture(scope="function")
def test_db(_base_session):
    db = _base_session
    school = School(name="Test School", slug="test-school", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    student_a = User(
        email="student_a@test.com", hashed_password=TEST_HASH,
        full_name="Student A", role="student", is_active=True,
        is_approved=True, school_id=school.id,
    )
    db.add(student_a)

    student_b = User(
        email="student_b@test.com", hashed_password=TEST_HASH,
        full_name="Student B", role="student", is_active=True,
        is_approved=True, school_id=school.id,
    )
    db.add(student_b)

    teacher = User(
        email="teacher@test.com", hashed_password=TEST_HASH,
        full_name="Teacher", role="teacher", is_active=True,
        is_approved=True, school_id=school.id,
    )
    db.add(teacher)
    db.commit()

    # Create minimal pathway data
    niveau = NiveauEtude(nom="9eme de base", ordre=1)
    db.add(niveau)
    db.commit()
    db.refresh(niveau)

    matiere = Matiere(niveau_etude_id=niveau.id, nom="Mathematiques")
    db.add(matiere)
    db.commit()
    db.refresh(matiere)

    chapter = ChapterPathway(matiere_id=matiere.id, nom="Chapitre Test", ordre=1)
    db.add(chapter)
    db.commit()
    db.refresh(chapter)

    yield db, school, student_a, student_b, teacher, chapter


@pytest.fixture(scope="function")
def client(test_db):
    return TestClient(app)


# ============================================================
# TEST 1: Student A CANNOT submit score for student B (IDOR fix)
# ============================================================
def test_01_student_cannot_score_other_student(test_db, client):
    """BEFORE fix: student A could POST /scores with eleve_id=B → 200 accepted.
    AFTER fix: student A POSTing with eleve_id=B → 403 denied."""
    db, school, student_a, student_b, teacher, chapter = test_db

    token_a = _login(client, "student_a@test.com")
    headers_a = _auth(token_a)

    resp = client.post("/api/pathway/scores", json={
        "eleve_id": student_b.id,
        "chapitre_id": chapter.id,
        "score": 85.0,
    }, headers=headers_a)

    assert resp.status_code == 403, (
        f"IDOR still present! Got {resp.status_code} instead of 403. "
        f"Response: {resp.json()}"
    )


# ============================================================
# TEST 2: Student CAN submit score for themselves
# ============================================================
def test_02_student_can_score_themselves(test_db, client):
    """Student submitting their own score must succeed."""
    db, school, student_a, student_b, teacher, chapter = test_db

    token_a = _login(client, "student_a@test.com")
    headers_a = _auth(token_a)

    resp = client.post("/api/pathway/scores", json={
        "eleve_id": student_a.id,
        "chapitre_id": chapter.id,
        "score": 72.0,
    }, headers=headers_a)

    assert resp.status_code == 200
    data = resp.json()
    assert data["eleve_id"] == student_a.id
    assert data["score"] == 72.0


# ============================================================
# TEST 3: Teacher CAN submit score for any student
# ============================================================
def test_03_teacher_can_score_any_student(test_db, client):
    """Teacher submitting a score for student B must succeed."""
    db, school, student_a, student_b, teacher, chapter = test_db

    token_t = _login(client, "teacher@test.com")
    headers_t = _auth(token_t)

    resp = client.post("/api/pathway/scores", json={
        "eleve_id": student_b.id,
        "chapitre_id": chapter.id,
        "score": 90.0,
    }, headers=headers_t)

    assert resp.status_code == 200
    data = resp.json()
    assert data["eleve_id"] == student_b.id
    assert data["score"] == 90.0
