"""
Tests de restriction par palier (découverte/excellence/etablissement).
Vérifie que les fonctionnalités IA sont correctement filtrées par palier.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from unittest.mock import patch, MagicMock

from app.models import User, School, Course, CourseStatus
from app.core.security import get_password_hash
from app.services.student_tier import get_student_tier, get_ai_feature_level

from tests.conftest import TEST_PASSWORD, TEST_HASH, _auth as _auth_header

# Fixtures test_db, client, admin_token, student_token come from conftest.py


# ── Tests fonctions utilitaires ──────────────────────────────

def test_student_tier_function(test_db):
    db, school, admin, student = test_db
    tier = get_student_tier(student, db)
    assert tier in ("decouverte", "excellence", "etablissement")


def test_ai_feature_level_function(test_db):
    db, school, admin, student = test_db
    level = get_ai_feature_level(student, db)
    assert level in ("basic", "adaptive", "curriculum_aligned")


# ── Tests dashboard ──────────────────────────────────────────

def test_dashboard_endpoint(client, test_db, student_token):
    resp = client.get("/api/learner/dashboard", headers=_auth_header(student_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "tier" in data
    assert data["tier"] in ("decouverte", "excellence", "etablissement")
    assert "courses" in data
    assert "daily_objective" in data
    assert "features" in data


def test_daily_objective_endpoint(client, test_db, student_token):
    resp = client.get("/api/learner/daily-objective", headers=_auth_header(student_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "tier" in data
    assert "message" in data
    assert "type" in data


def test_recommended_path_endpoint(client, test_db, student_token):
    resp = client.get("/api/learner/recommended-path", headers=_auth_header(student_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "tier" in data
    assert "description" in data
    assert "courses" in data
    assert "next_step" in data


# ── Tests placement ──────────────────────────────────────────

def test_placement_tests_list(client, test_db):
    resp = client.get("/api/placement/tests")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


# ── Tests restrictions IA ────────────────────────────────────

def test_student_ai_ask_allowed(client, test_db, student_token):
    """Student peut utiliser /ai/ask (questions simples) — pas de 403."""
    with patch("app.ai.RAGService") as MockRAG:
        mock_rag = MagicMock()
        mock_rag.ask.return_value = {"answer": "test", "sources": []}
        MockRAG.return_value = mock_rag

        resp = client.post(
            "/api/ai/ask",
            json={"question": "Qu'est-ce que la photosynthèse ?"},
            headers=_auth_header(student_token),
        )
        assert resp.status_code in (200, 402), f"Expected 200/402, got {resp.status_code}: {resp.text}"


def test_student_ai_explain_allowed(client, test_db, student_token):
    """Student peut utiliser /ai/explic — pas de 403."""
    with patch("app.ai.RAGService") as MockRAG:
        mock_rag = MagicMock()
        mock_rag.explain.return_value = {"answer": "explication test", "sources": []}
        MockRAG.return_value = mock_rag

        resp = client.post(
            "/api/ai/explain",
            json={"question": "Explique la photosynthèse"},
            headers=_auth_header(student_token),
        )
        assert resp.status_code in (200, 402), f"Expected 200/402, got {resp.status_code}: {resp.text}"


def test_student_ai_exercises_blocked(client, test_db, student_token):
    """Découverte ne peut PAS utiliser /ai/exercises (excellence+)."""
    resp = client.post(
        "/api/ai/exercises",
        params={"topic": "Mathématiques", "num_exercises": 3},
        headers=_auth_header(student_token),
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
    assert "paliers" in resp.json()["detail"].lower() or "excellence" in resp.json()["detail"].lower()


def test_student_ai_generate_blocked(client, test_db, student_token):
    """Découverte ne peut PAS utiliser /ai/generate (établissement)."""
    resp = client.post(
        "/api/ai/generate",
        json={"type": "homework", "subject": "Maths", "level": "2ème année", "trimester": "T1", "prompt": "Génère un devoir"},
        headers=_auth_header(student_token),
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
    assert "établissement" in resp.json()["detail"].lower()
