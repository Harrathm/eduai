"""
Tests de vérification — Suite audit 01/08/2026
===============================================
Point 1: Decimal(10,2) — précision monétaire exacte
Point 3: Script de réconciliation — détection transactions orphelines

Exécution: python -m pytest tests/test_decimal_reconciliation.py -v
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import (
    User, School, Course, Module, Lesson,
    CourseStatus, CourseEnrollment, CoursePurchase,
    WalletTransaction, WalletPool, Transaction, TransactionType, Currency,
)
from app.core.security import get_password_hash
from app.services.wallet import credit_dt, debit_dt, get_dt_balance

TEST_PASSWORD = "password123"
TEST_HASH = get_password_hash(TEST_PASSWORD)


def _create_user(db, email, role, school_id, niveau_scolaire=None):
    user = User(
        email=email, hashed_password=TEST_HASH, full_name=f"User {email}",
        role=role, is_active=True, school_id=school_id,
        niveau_scolaire=niveau_scolaire,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_course(db, school_id, author_id, price=Decimal("50.00")):
    course = Course(
        title="Test Paid Course", slug=f"test-paid-{price}",
        school_id=school_id, author_id=author_id,
        price=price, price_dt=Decimal("50.00"), price_tokens=0,
        visibility="public_catalog", status=CourseStatus.PUBLISHED,
        is_published=True, niveau_scolaire="9eme de base",
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def _login(client, email):
    resp = client.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
    return resp.json().get("access_token")


# ══════════════════════════════════════════════════════════════════════════════
# POINT 1 — Decimal(10,2) précision monétaire
# ══════════════════════════════════════════════════════════════════════════════

class TestDecimalPrecision:
    """
    Vérifie que toutes les opérations monétaires utilisent Decimal
    et que l'accumulation de 50+ transactions n'introduit aucune erreur.
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

        school = School(name="School DEC", slug="school-dec", school_type="real")
        db.add(school)
        db.commit()
        db.refresh(school)

        teacher = _create_user(db, "teacher_dec@test.com", "teacher", school.id)
        student = _create_user(db, "student_dec@test.com", "student", school.id, niveau_scolaire="9eme de base")

        self.db = db
        self.student = student
        self.school = school
        self.teacher = teacher

        yield

        app.dependency_overrides.clear()
        db.close()

    def test_type_decimal_at_every_step(self):
        """Vérifie que Decimal est utilisé à chaque étape critique."""
        # 1. Crédit
        tx = credit_dt(self.db, self.student.id, Decimal("100.00"), source="test")
        assert isinstance(tx.amount, Decimal), f"WalletTransaction.amount doit être Decimal, obtenu {type(tx.amount)}"

        # 2. Solde
        balance = get_dt_balance(self.db, self.student.id)
        assert isinstance(balance, Decimal), f"get_dt_balance() doit retourner Decimal, obtenu {type(balance)}"

        # 3. Débit
        tx2 = debit_dt(self.db, self.student.id, Decimal("14.99"), source="test", commit=True)
        assert isinstance(tx2.amount, Decimal), f"Débit amount doit être Decimal, obtenu {type(tx2.amount)}"

        # 4. Solde après débit
        balance_after = get_dt_balance(self.db, self.student.id)
        assert isinstance(balance_after, Decimal), f"Solde après débit doit être Decimal, obtenu {type(balance_after)}"
        assert balance_after == Decimal("85.01"), f"Solde devrait être 85.01, obtenu {balance_after}"

    def test_50_transactions_exact_accumulation(self):
        """50 transactions mélangées (débits/crédits) → solde exact au centime."""
        credit_dt(self.db, self.student.id, Decimal("5000.00"), source="test")

        # Montants variés : crédits et débits mélangés
        amounts = [
            (Decimal("14.99"), "debit"), (Decimal("0.10"), "debit"),
            (Decimal("999.99"), "debit"), (Decimal("0.01"), "debit"),
            (Decimal("50.00"), "debit"), (Decimal("0.50"), "debit"),
            (Decimal("250.00"), "debit"), (Decimal("0.25"), "debit"),
            (Decimal("100.00"), "debit"), (Decimal("0.99"), "debit"),
            (Decimal("200.00"), "credit"), (Decimal("10.10"), "credit"),
            (Decimal("5.55"), "debit"), (Decimal("99.99"), "debit"),
            (Decimal("1.01"), "debit"), (Decimal("50.50"), "debit"),
            (Decimal("0.33"), "debit"), (Decimal("75.00"), "debit"),
            (Decimal("25.25"), "debit"), (Decimal("150.00"), "debit"),
            (Decimal("0.05"), "debit"), (Decimal("300.00"), "debit"),
            (Decimal("12.34"), "debit"), (Decimal("67.89"), "debit"),
            (Decimal("0.75"), "debit"), (Decimal("45.00"), "debit"),
            (Decimal("33.33"), "debit"), (Decimal("22.22"), "debit"),
            (Decimal("88.88"), "debit"), (Decimal("11.11"), "debit"),
            (Decimal("55.55"), "debit"), (Decimal("44.44"), "debit"),
            (Decimal("66.66"), "debit"), (Decimal("77.77"), "debit"),
            (Decimal("9.99"), "debit"), (Decimal("8.88"), "debit"),
            (Decimal("7.77"), "debit"), (Decimal("6.66"), "debit"),
            (Decimal("5.55"), "debit"), (Decimal("4.44"), "debit"),
            (Decimal("3.33"), "debit"), (Decimal("2.22"), "debit"),
            (Decimal("1.11"), "debit"), (Decimal("100.00"), "credit"),
            (Decimal("50.00"), "credit"), (Decimal("25.00"), "credit"),
            (Decimal("10.00"), "credit"), (Decimal("5.00"), "credit"),
            (Decimal("2.00"), "credit"), (Decimal("1.00"), "credit"),
        ]

        expected_balance = Decimal("5000.00")
        for amount, op in amounts:
            if op == "debit":
                debit_dt(self.db, self.student.id, amount, source="test", commit=True)
                expected_balance -= amount
            else:
                credit_dt(self.db, self.student.id, amount, source="test", commit=True)
                expected_balance += amount

        # Solde final exact
        balance = get_dt_balance(self.db, self.student.id)
        assert balance == expected_balance, (
            f"Après 50 transactions, solde devrait être {expected_balance}, "
            f"obtenu {balance} (écart: {balance - expected_balance})"
        )

        # Vérifier en sommant directement le ledger
        from sqlalchemy import func
        ledger_sum = self.db.query(
            func.coalesce(func.sum(WalletTransaction.amount), 0)
        ).filter(
            WalletTransaction.user_id == self.student.id,
            WalletTransaction.pool == WalletPool.DT_PURCHASED,
        ).scalar()
        ledger_decimal = Decimal(str(ledger_sum))

        assert balance == ledger_decimal, (
            f"Solde calculé ({balance}) != somme ledger ({ledger_decimal})"
        )

    def test_decimal_not_float_in_api_response(self):
        """L'API retourne des montants avec précision Decimal (2 décimales exactes)."""
        credit_dt(self.db, self.student.id, Decimal("100.00"), source="test")

        client = TestClient(app)
        token = _login(client, self.student.email)
        resp = client.get(
            "/api/wallet/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        # Le solde dt_purchased doit être exactement 100.00 (pas 99.9999999 ou 100.0000001)
        dt_pool = next(p for p in body["pools"] if p["pool"] == "dt_purchased")
        assert dt_pool["balance"] == 100.0, f"Solde devrait être 100.0, obtenu {dt_pool['balance']}"
        # Vérifier la précision : le total doit être un nombre avec exactement 2 décimales
        total_str = f"{body['total']:.2f}"
        assert float(total_str) == body["total"], (
            f"Total doit être arrondi à 2 décimales: {body['total']}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# POINT 3 — Script de réconciliation
# ══════════════════════════════════════════════════════════════════════════════

RECONCILIATION_SQL = """
SELECT wt.id, wt.user_id, wt.amount, wt.created_at, wt.metadata
FROM wallet_transactions wt
LEFT JOIN course_purchases cp ON cp.transaction_id = CAST(wt.id AS TEXT)
WHERE wt.metadata IS NOT NULL
  AND wt.metadata->>'source' = 'purchase'
  AND wt.amount < 0
  AND cp.id IS NULL;
"""


class TestReconciliation:
    """
    Simule le bug historique (débit sans CoursePurchase) et vérifie
    que le script de réconciliation le détecte correctement.
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

        school = School(name="School REC", slug="school-rec", school_type="real")
        db.add(school)
        db.commit()
        db.refresh(school)

        teacher = _create_user(db, "teacher_rec@test.com", "teacher", school.id)
        student = _create_user(db, "student_rec@test.com", "student", school.id, niveau_scolaire="9eme de base")

        self.db = db
        self.student = student
        self.school = school
        self.teacher = teacher

        yield

        app.dependency_overrides.clear()
        db.close()

    def test_orphan_detected(self):
        """Une WalletTransaction de débit sans CoursePurchase est détectée."""
        # Simuler le bug : crédit puis débit orphelin (pas de CoursePurchase)
        credit_dt(self.db, self.student.id, Decimal("100.00"), source="test")
        orphan_tx = debit_dt(
            self.db, self.student.id, Decimal("50.00"),
            source="purchase", reason="Achat cours: Cours Orphelin",
            commit=True,
        )

        # Exécuter le script de réconciliation (adapter pour SQLite : JSON support)
        # SQLite utilise json_extract au lieu de ->
        sql_sqlite = """
        SELECT wt.id, wt.user_id, wt.amount, wt.created_at, wt.metadata
        FROM wallet_transactions wt
        LEFT JOIN course_purchases cp ON cp.transaction_id = CAST(wt.id AS TEXT)
        WHERE wt.metadata IS NOT NULL
          AND json_extract(wt.metadata, '$.source') = 'purchase'
          AND wt.amount < 0
          AND cp.id IS NULL;
        """
        rows = self.db.execute(text(sql_sqlite)).fetchall()

        assert len(rows) >= 1, (
            f"Le script devrait détecter au moins 1 transaction orpheline, "
            f"trouvé {len(rows)}"
        )

        # Vérifier que c'est bien notre transaction orpheline
        orphan_ids = [row[0] for row in rows]
        assert orphan_tx.id in orphan_ids, (
            f"Transaction orpheline {orphan_tx.id} non détectée. "
            f"IDs trouvés: {orphan_ids}"
        )

        # Vérifier le montant
        for row in rows:
            if row[0] == orphan_tx.id:
                assert Decimal(str(row[2])) == Decimal("-50.00"), (
                    f"Montant orpheline devrait être -50.00, obtenu {row[2]}"
                )

    def test_no_false_positives(self):
        """Une transaction normale (débit + CoursePurchase) n'est PAS détectée."""
        credit_dt(self.db, self.student.id, Decimal("100.00"), source="test")

        # Débit normaal avec CoursePurchase correspondant
        normal_tx = debit_dt(
            self.db, self.student.id, Decimal("30.00"),
            source="purchase", reason="Achat cours: Cours Normal",
            commit=True,
        )

        # Créer le CoursePurchase correspondant (transaction_id = id du wallet tx)
        purchase = CoursePurchase(
            student_id=self.student.id,
            course_id=1,  # fake course ID
            amount_paid=Decimal("30.00"),
            currency="TND",
            transaction_id=str(normal_tx.id),
        )
        self.db.add(purchase)
        self.db.commit()

        # Exécuter le script
        sql_sqlite = """
        SELECT wt.id, wt.user_id, wt.amount, wt.created_at, wt.metadata
        FROM wallet_transactions wt
        LEFT JOIN course_purchases cp ON cp.transaction_id = CAST(wt.id AS TEXT)
        WHERE wt.metadata IS NOT NULL
          AND json_extract(wt.metadata, '$.source') = 'purchase'
          AND wt.amount < 0
          AND cp.id IS NULL;
        """
        rows = self.db.execute(text(sql_sqlite)).fetchall()

        # Notre transaction normale ne devrait PAS apparaître
        detected_ids = [row[0] for row in rows]
        assert normal_tx.id not in detected_ids, (
            f"Transaction normale {normal_tx.id} ne devrait PAS être détectée "
            f"comme orpheline (faux positif!)"
        )

    def test_mixed_scenario(self):
        """Scénario mixte : 1 orpheline + 1 normale → seul l'orphelin est trouvé."""
        credit_dt(self.db, self.student.id, Decimal("200.00"), source="test")

        # Transaction orpheline (bug historique)
        orphan_tx = debit_dt(
            self.db, self.student.id, Decimal("50.00"),
            source="purchase", reason="Achat cours: Cours Orphelin",
            commit=True,
        )

        # Transaction normale
        normal_tx = debit_dt(
            self.db, self.student.id, Decimal("30.00"),
            source="purchase", reason="Achat cours: Cours Normal",
            commit=True,
        )
        purchase = CoursePurchase(
            student_id=self.student.id,
            course_id=1,
            amount_paid=Decimal("30.00"),
            currency="TND",
            transaction_id=str(normal_tx.id),
        )
        self.db.add(purchase)
        self.db.commit()

        # Exécuter le script
        sql_sqlite = """
        SELECT wt.id, wt.user_id, wt.amount, wt.created_at, wt.metadata
        FROM wallet_transactions wt
        LEFT JOIN course_purchases cp ON cp.transaction_id = CAST(wt.id AS TEXT)
        WHERE wt.metadata IS NOT NULL
          AND json_extract(wt.metadata, '$.source') = 'purchase'
          AND wt.amount < 0
          AND cp.id IS NULL;
        """
        rows = self.db.execute(text(sql_sqlite)).fetchall()

        detected_ids = [row[0] for row in rows]

        # Seule l'orpheline doit être trouvée
        assert orphan_tx.id in detected_ids, "Transaction orpheline non détectée"
        assert normal_tx.id not in detected_ids, "Transaction normale = faux positif"
        assert len(rows) == 1, f"Exactement 1 orpheline attendue, {len(rows)} trouvée(s)"
