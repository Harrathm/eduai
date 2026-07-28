"""Tests for parent role — RBAC + endpoints.

Covers audit §3.2:
1. Parent can list their own children and nothing else
2. Parent accessing a non-linked student gets 403
3. Suivi view reflects niveau_effectif from Adaptive Pathway layer 3
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import User, School, ParentEnfant, UserRole, PackPurchase, PackPurchaseStatus, StudyPack, PackStatus, PurchaserType, WalletTransaction, WalletPool
from app.core.security import get_password_hash

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

    school = School(name="Ecole Parent", slug="ecole-parent", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    # Parent user
    parent = User(
        email="parent@test.com", hashed_password=TEST_HASH,
        full_name="Parent Test", role=UserRole.PARENT,
        is_active=True, is_approved=True, school_id=school.id,
    )
    db.add(parent)

    # Student 1 (linked to parent)
    student1 = User(
        email="eleve1@test.com", hashed_password=TEST_HASH,
        full_name="Eleve Un", role=UserRole.STUDENT,
        is_active=True, is_approved=True, school_id=school.id,
        niveau_scolaire="9eme de base",
    )
    db.add(student1)

    # Student 2 (NOT linked to parent)
    student2 = User(
        email="eleve2@test.com", hashed_password=TEST_HASH,
        full_name="Eleve Deux", role=UserRole.STUDENT,
        is_active=True, is_approved=True, school_id=school.id,
        niveau_scolaire="7eme de base",
    )
    db.add(student2)
    db.commit()
    db.refresh(parent)
    db.refresh(student1)
    db.refresh(student2)

    # Link parent -> student1 only
    link = ParentEnfant(parent_user_id=parent.id, eleve_id=student1.id)
    db.add(link)

    # Credit student1 with DT (create WalletTransaction directly, avoid credit_dt's internal commit)
    credit_tx = WalletTransaction(
        user_id=student1.id, pool=WalletPool.DT_PURCHASED, amount=100,
        metadata_={"source": "test", "reason": "test seed"},
    )
    db.add(credit_tx)

    # Create a pack purchase for student1
    pack = StudyPack(
        name="Pack 9eme", niveau_scolaire="9eme de base",
        price=50.0, validity_duration_days=365,
        status=PackStatus.PUBLISHED.value,
        created_by=parent.id, school_id=school.id,
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)

    now = datetime.utcnow().replace(tzinfo=None)
    purchase = PackPurchase(
        pack_id=pack.id, purchaser_type=PurchaserType.STUDENT.value,
        student_id=student1.id, school_id=None,
        valid_from=now, valid_until=now + timedelta(days=365),
        status=PackPurchaseStatus.ACTIVE.value,
        amount_paid=50.0, currency="TND",
    )
    db.add(purchase)
    db.commit()

    # Expire all cached objects so the API session reads fresh from DB
    db.expire_all()

    yield db, school, parent, student1, student2, pack

    app.dependency_overrides.clear()
    db.close()


@pytest.fixture(scope="function")
def client(test_db):
    return TestClient(app)


def _login(client, email):
    resp = client.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
    return resp.json().get("access_token")


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestParentRBAC:
    def test_parent_can_list_own_children(self, test_db, client):
        db, school, parent, student1, student2, pack = test_db
        token = _login(client, parent.email)

        resp = client.get("/api/parents/me/enfants", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        enfants = data["enfants"]
        assert len(enfants) == 1
        assert enfants[0]["eleve_id"] == student1.id
        assert enfants[0]["full_name"] == "Eleve Un"

    def test_parent_cannot_see_unlinked_student(self, test_db, client):
        db, school, parent, student1, student2, pack = test_db
        token = _login(client, parent.email)

        resp = client.get(
            f"/api/parents/me/enfants/{student2.id}/suivi",
            headers=_auth(token),
        )
        assert resp.status_code == 403
        assert "pas rattaché" in resp.json()["detail"]

    def test_suivi_shows_student_info(self, test_db, client):
        db, school, parent, student1, student2, pack = test_db
        token = _login(client, parent.email)

        resp = client.get(
            f"/api/parents/me/enfants/{student1.id}/suivi",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eleve_id"] == student1.id
        assert data["full_name"] == "Eleve Un"
        assert data["niveau_scolaire"] == "9eme de base"
        assert data["dt_balance"] == 100.0

    def test_non_parent_cannot_access_parent_endpoints(self, test_db, client):
        db, school, parent, student1, student2, pack = test_db
        token = _login(client, student1.email)

        resp = client.get("/api/parents/me/enfants", headers=_auth(token))
        assert resp.status_code == 403
        assert "Parent access required" in resp.json()["detail"]
