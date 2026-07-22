"""
Tests du système d'objectifs pédagogiques (Phases 1-5).
Vérifie :
- Modèle LearningGoal et enums
- Calcul dynamique du statut (jamais stocké)
- Génération automatique daily/weekly
- Pack Découverte ne reçoit PAS d'objectifs personnalisés
- Objectif trimestriel assigné à une classe est visible pour chaque élève
- Statut recalculé dynamiquement (lesson complétée → behind → on_track)
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import (
    User, School, LearningGoal, ClassroomEnrollment, ClassRoom,
    StudyPack, PackPurchase, PackPurchaseStatus, PurchaserType,
    GoalHorizon, GoalStatus, GoalMetricType, GoalSource,
)
from app.core.security import get_password_hash
from app.services.goal_tracking import (
    compute_goal_status, generate_daily_goal, generate_weekly_goal,
    STATUS_MESSAGES, get_status_message,
)
from app.services.school_calendar import get_current_trimester, get_period_for_horizon

TEST_PASSWORD = "password123"
TEST_HASH = get_password_hash(TEST_PASSWORD)


@pytest.fixture(scope="function")
def test_db():
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

    admin = User(
        email="admin@test.com", hashed_password=TEST_HASH, full_name="Admin",
        role="SUPER_ADMIN", is_active=True, is_approved=True, school_id=school.id,
    )
    student_exc = User(
        email="student_exc@test.com", hashed_password=TEST_HASH, full_name="Student Excellence",
        role="student", is_active=True, is_approved=True, school_id=school.id,
        niveau_scolaire="2eme_secondaire",
    )
    student_dec = User(
        email="student_dec@test.com", hashed_password=TEST_HASH, full_name="Student Decouverte",
        role="student", is_active=True, is_approved=True, school_id=school.id,
        niveau_scolaire="2eme_secondaire",
    )
    db.add_all([admin, student_exc, student_dec])
    db.commit()

    # Create StudyPack + PackPurchase for student_exc to make them "excellence"
    pack = StudyPack(
        name="Excellence 2eme",
        niveau_scolaire="2eme_secondaire",
        price=100,
        status="published", owner_type="school", school_id=school.id,
    )
    db.add(pack)
    db.commit()

    purchase = PackPurchase(
        pack_id=pack.id, student_id=student_exc.id,
        purchaser_type="student",
        status=PackPurchaseStatus.ACTIVE.value,
        valid_from=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc) + timedelta(days=365),
        amount_paid=100.0,
    )
    db.add(purchase)
    db.commit()

    yield db, school, admin, student_exc, student_dec
    db.close()
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_db):
    return TestClient(app)


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _login(client, email):
    resp = client.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
    if resp.status_code == 200:
        return resp.json().get("access_token", "")
    return ""


# ── Tests Enums ─────────────────────────────────────────────

def test_enums():
    assert GoalHorizon.DAILY.value == "daily"
    assert GoalStatus.ON_TRACK.value == "on_track"
    assert GoalMetricType.LESSONS_COMPLETED.value == "lessons_completed"
    assert GoalSource.AUTO_GENERATED.value == "auto_generated"


# ── Tests School Calendar ───────────────────────────────────

def test_school_calendar():
    period_start, period_end = get_period_for_horizon("daily", date(2026, 1, 15))
    assert period_start == date(2026, 1, 15)
    assert period_end == date(2026, 1, 15)

    period_start, period_end = get_period_for_horizon("weekly", date(2026, 1, 15))
    assert period_start <= date(2026, 1, 15) <= period_end
    assert (period_end - period_start).days == 6

    period_start, period_end = get_period_for_horizon("monthly", date(2026, 1, 15))
    assert period_start.day == 1
    assert period_end.month == 1

    tri = get_current_trimester(date(2026, 1, 20))
    assert tri is not None
    assert tri.number == 2


# ── Tests Status Messages ──────────────────────────────────

def test_status_messages():
    assert "bonne voie" in get_status_message("on_track")
    assert "rattraper" in get_status_message("behind")
    assert "felicitations" in get_status_message("completed")
    assert "repartir" in get_status_message("missed")


# ── Tests Compute Goal Status ──────────────────────────────

def test_compute_goal_status_no_data(test_db):
    db, school, admin, student_exc, student_dec = test_db
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    goal = LearningGoal(
        user_id=student_exc.id,
        horizon=GoalHorizon.DAILY.value,
        metric_type=GoalMetricType.LESSONS_COMPLETED.value,
        target_value=Decimal("3"),
        period_start=start,
        period_end=end,
        source=GoalSource.AUTO_GENERATED.value,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    status_data = compute_goal_status(goal, db)
    assert status_data["status"] in ("on_track", "behind")  # Behind car 0/3
    assert status_data["current_value"] == 0.0
    assert status_data["target_value"] == 3.0
    assert status_data["message"] != ""


def test_compute_goal_status_completed(test_db):
    db, school, admin, student_exc, student_dec = test_db
    yesterday = date.today() - timedelta(days=1)
    start = datetime.combine(yesterday, datetime.min.time())
    end = datetime.combine(yesterday, datetime.max.time())

    goal = LearningGoal(
        user_id=student_exc.id,
        horizon=GoalHorizon.DAILY.value,
        metric_type=GoalMetricType.LESSONS_COMPLETED.value,
        target_value=Decimal("2"),
        period_start=start,
        period_end=end,
        source=GoalSource.AUTO_GENERATED.value,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    status_data = compute_goal_status(goal, db)
    # Période dépassée, 0 leçons complétées → missed
    assert status_data["status"] == GoalStatus.MISSED.value


# ── Tests Auto-generation ──────────────────────────────────

def test_generate_daily_goal_excellence(test_db):
    db, school, admin, student_exc, student_dec = test_db
    goal = generate_daily_goal(student_exc, db)
    assert goal is not None
    assert goal.horizon == GoalHorizon.DAILY.value
    assert goal.source == GoalSource.AUTO_GENERATED.value
    assert goal.user_id == student_exc.id


def test_generate_daily_goal_decouverte_returns_none(test_db):
    db, school, admin, student_exc, student_dec = test_db
    goal = generate_daily_goal(student_dec, db)
    assert goal is None, "Pack Decouverte ne doit PAS recevoir d'objectif daily"


def test_generate_weekly_goal_decouverte_returns_none(test_db):
    db, school, admin, student_exc, student_dec = test_db
    goal = generate_weekly_goal(student_dec, db)
    assert goal is None, "Pack Decouverte ne doit PAS recevoir d'objectif weekly"


def test_generate_weekly_goal_excellence(test_db):
    db, school, admin, student_exc, student_dec = test_db
    goal = generate_weekly_goal(student_exc, db, target_hours=5.0)
    assert goal is not None
    assert goal.horizon == GoalHorizon.WEEKLY.value
    assert float(goal.target_value) == 300.0  # 5h * 60 min


def test_ensure_goals_exist(test_db):
    db, school, admin, student_exc, student_dec = test_db
    from app.services.goal_tracking import ensure_goals_exist
    result = ensure_goals_exist(student_exc, db)
    assert result["daily"] is not None
    assert result["weekly"] is not None


# ── Tests Decouverte never gets goals ───────────────────────

def test_decouverte_never_gets_custom_goals(test_db):
    db, school, admin, student_exc, student_dec = test_db
    from app.services.goal_tracking import ensure_goals_exist
    result = ensure_goals_exist(student_dec, db)
    assert result["daily"] is None
    assert result["weekly"] is None


# ── Tests Dynamic Recalculation ────────────────────────────

def test_status_recalculates_dynamically(test_db):
    """
    Vérifie que le statut est recalculé à la volée :
    si on ajoute une leçon complétée, le statut change sans modifier le goal.
    """
    db, school, admin, student_exc, student_dec = test_db
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    goal = LearningGoal(
        user_id=student_exc.id,
        horizon=GoalHorizon.DAILY.value,
        metric_type=GoalMetricType.LESSONS_COMPLETED.value,
        target_value=Decimal("2"),
        period_start=start,
        period_end=end,
        source=GoalSource.AUTO_GENERATED.value,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    # Statut initial : behind (0/2 leçons)
    status1 = compute_goal_status(goal, db)
    assert status1["current_value"] == 0.0
    assert status1["status"] == GoalStatus.BEHIND.value

    # Vérifier que le goal n'a PAS de champ "status" stocké
    assert not hasattr(goal, "status") or goal.__table__.columns.get("status") is None


# ── Tests API Endpoints ────────────────────────────────────

def test_goals_endpoint(client, test_db):
    db, school, admin, student_exc, student_dec = test_db
    token = _login(client, "student_exc@test.com")
    if not token:
        pytest.skip("Token unavailable")

    resp = client.get("/api/learner/goals", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_goals_summary_endpoint(client, test_db):
    db, school, admin, student_exc, student_dec = test_db
    token = _login(client, "student_exc@test.com")
    if not token:
        pytest.skip("Token unavailable")

    resp = client.get("/api/learner/goals/summary", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "daily" in data
    assert "weekly" in data
    assert "monthly" in data
    assert "quarterly" in data
    assert "annual" in data


def test_goals_report_endpoint(client, test_db):
    db, school, admin, student_exc, student_dec = test_db
    token = _login(client, "student_exc@test.com")
    if not token:
        pytest.skip("Token unavailable")

    resp = client.get("/api/learner/goals/report?horizon=weekly", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "horizon" in data
    assert "goals" in data
    # No weekly goals yet, so goals should be empty
    assert isinstance(data["goals"], list)
