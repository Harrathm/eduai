"""
Tests de garde-fou backend : achat de pack deja inclus par l'ecole.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import (
    User, School, StudyPack, PackPurchase, PackPurchaseStatus, PackStatus,
    PurchaserType, Transaction, WalletTransaction, WalletPool,
)
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

    school = School(name="Ecole Test", slug="ecole-test", subscription_tier="free")
    db.add(school)
    db.commit()
    db.refresh(school)

    student_9eme = User(
        email="student_9eme@test.com",
        hashed_password=TEST_HASH,
        full_name="Student 9eme",
        role="student",
        is_active=True,
        is_approved=True,
        school_id=school.id,
        niveau_scolaire="9eme de base",
    )
    db.add(student_9eme)
    db.commit()
    db.refresh(student_9eme)

    # Credit DT via WalletTransaction (append-only ledger)
    credit_9 = WalletTransaction(
        user_id=student_9eme.id, pool=WalletPool.DT_PURCHASED, amount=200,
        metadata_={"source": "test", "reason": "test seed"},
    )
    db.add(credit_9)

    student_7eme = User(
        email="student_7eme@test.com",
        hashed_password=TEST_HASH,
        full_name="Student 7eme",
        role="student",
        is_active=True,
        is_approved=True,
        school_id=school.id,
        niveau_scolaire="7eme de base",
    )
    db.add(student_7eme)
    db.commit()
    db.refresh(student_7eme)

    # Credit DT via WalletTransaction (append-only ledger)
    credit_7 = WalletTransaction(
        user_id=student_7eme.id, pool=WalletPool.DT_PURCHASED, amount=200,
        metadata_={"source": "test", "reason": "test seed"},
    )
    db.add(credit_7)

    pack_9 = StudyPack(
        name="Pack 9eme",
        niveau_scolaire="9eme de base",
        price=50.0,
        validity_duration_days=365,
        status=PackStatus.PUBLISHED.value,
        created_by=student_9eme.id,
        school_id=school.id,
    )
    db.add(pack_9)
    db.commit()
    db.refresh(pack_9)

    pack_7 = StudyPack(
        name="Pack 7eme",
        niveau_scolaire="7eme de base",
        price=30.0,
        validity_duration_days=365,
        status=PackStatus.PUBLISHED.value,
        created_by=student_7eme.id,
        school_id=school.id,
    )
    db.add(pack_7)
    db.commit()
    db.refresh(pack_7)

    now = datetime.now(timezone.utc)
    school_purchase = PackPurchase(
        pack_id=pack_9.id,
        purchaser_type=PurchaserType.SCHOOL.value,
        school_id=school.id,
        valid_from=now,
        valid_until=now + timedelta(days=365),
        status=PackPurchaseStatus.ACTIVE.value,
        amount_paid=pack_9.price,
        currency=pack_9.currency,
    )
    db.add(school_purchase)
    db.commit()

    yield db, school, student_9eme, student_7eme, pack_9, pack_7

    app.dependency_overrides.clear()
    db.close()


@pytest.fixture(scope="function")
def client(test_db):
    return TestClient(app)


@pytest.fixture(scope="function")
def student_9eme_token(client, test_db):
    resp = client.post("/auth/login", data={"username": "student_9eme@test.com", "password": TEST_PASSWORD})
    data = resp.json()
    assert "access_token" in data, f"Login failed: {resp.status_code} {data}"
    return data["access_token"]


@pytest.fixture(scope="function")
def student_7eme_token(client, test_db):
    resp = client.post("/auth/login", data={"username": "student_7eme@test.com", "password": TEST_PASSWORD})
    data = resp.json()
    assert "access_token" in data, f"Login failed: {resp.status_code} {data}"
    return data["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestPackPurchaseGuard:

    def test_cannot_purchase_pack_included_by_school(self, test_db, client, student_9eme_token):
        """Achat rejete si l'ecole a deja un pack actif pour le meme niveau."""
        db, school, student_9eme, student_7eme, pack_9, pack_7 = test_db
        from app.services.wallet import get_dt_balance
        balance_before = get_dt_balance(db, student_9eme.id)

        resp = client.post(
            f"/api/packs/{pack_9.id}/purchase",
            headers=_auth(student_9eme_token),
        )

        assert resp.status_code == 400, f"Attendu 400, recu {resp.status_code}: {resp.text}"
        detail = resp.json().get("detail", "")
        has_keyword = any(kw in detail.lower() for kw in ["ecole", "\u00e9cole", "deja", "d\u00e9j\u00e0", "besoin"])
        assert has_keyword, f"Le message doit mentionner l'ecole ou deja: {detail}"

        assert get_dt_balance(db, student_9eme.id) == balance_before, (
            f"Solde inchange. Avant: {balance_before}, Apres: {get_dt_balance(db, student_9eme.id)}"
        )

        transactions_count = db.query(Transaction).filter(Transaction.user_id == student_9eme.id).count()
        assert transactions_count == 0, f"Aucune Transaction creee. Trouve: {transactions_count}"

        purchases_count = db.query(PackPurchase).filter(PackPurchase.student_id == student_9eme.id).count()
        assert purchases_count == 0, f"Aucun PackPurchase STUDENT. Trouve: {purchases_count}"

    def test_can_purchase_pack_not_included_by_school(self, test_db, client, student_7eme_token):
        """Achat reussi si l'ecole n'a pas de pack actif pour le niveau de l'eleve."""
        db, school, student_9eme, student_7eme, pack_9, pack_7 = test_db
        from app.services.wallet import get_dt_balance
        balance_before = get_dt_balance(db, student_7eme.id)

        resp = client.post(
            f"/api/packs/{pack_7.id}/purchase",
            headers=_auth(student_7eme_token),
        )

        assert resp.status_code == 200, f"Attendu 200, recu {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["amount_paid"] == 30.0

        assert get_dt_balance(db, student_7eme.id) == balance_before - 30.0, (
            f"Solde debite. Avant: {balance_before}, Apres: {get_dt_balance(db, student_7eme.id)}"
        )

        purchase = db.query(PackPurchase).filter(
            PackPurchase.student_id == student_7eme.id,
            PackPurchase.pack_id == pack_7.id,
        ).first()
        assert purchase is not None
        assert purchase.purchaser_type == PurchaserType.STUDENT.value

        transaction = db.query(Transaction).filter(
            Transaction.user_id == student_7eme.id,
            Transaction.reference_id == f"pack_{pack_7.id}",
        ).first()
        assert transaction is not None
