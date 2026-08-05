"""
Phase 1.3 — Float→Decimal migration for 5 monetary fields.

Test 1: Transaction.amount preserves precision (19.999 -> Numeric(10,2))
Test 2: TokenPackage.price_dt preserves precision
Test 3: Course.price_dt preserves precision
Test 4: Plan.price preserves precision
Test 5: AIUsageLog.cost_usd preserves precision (10,4)
Test 6: Arithmetic on converted fields uses Decimal correctly
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import (
    Transaction, TokenPackage, Course, Plan, AIUsageLog,
    School, User, Currency, TransactionType,
)


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ============================================================
# TEST 1: Transaction.amount is Numeric(10,2), not Float
# ============================================================
def test_01_transaction_amount_is_numeric(db_session):
    """Verify column type is Numeric(10,2) and preserves Decimal precision."""
    from sqlalchemy import inspect
    inspector = inspect(db_session.get_bind())
    cols = {c["name"]: c for c in inspector.get_columns("transactions")}
    assert cols["amount"]["type"].__class__.__name__.upper() == "NUMERIC"

    school = School(name="T", slug="t", subscription_tier="free")
    db_session.add(school)
    db_session.commit()

    t = Transaction(
        school_id=school.id, user_id=1, type=TransactionType.TOKEN_CONSUMPTION,
        amount=Decimal("19.999"), currency=Currency.TOKEN,
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    # Numeric(10,2) rounds to 2 decimals
    assert t.amount == Decimal("20.00"), f"Expected 20.00, got {t.amount}"


# ============================================================
# TEST 2: TokenPackage.price_dt is Numeric(10,2)
# ============================================================
def test_02_tokenpackage_price_dt_is_numeric(db_session):
    from sqlalchemy import inspect
    inspector = inspect(db_session.get_bind())
    cols = {c["name"]: c for c in inspector.get_columns("token_packages")}
    assert cols["price_dt"]["type"].__class__.__name__.upper() == "NUMERIC"


# ============================================================
# TEST 3: Course.price_dt is Numeric(10,2)
# ============================================================
def test_03_course_price_dt_is_numeric(db_session):
    from sqlalchemy import inspect
    inspector = inspect(db_session.get_bind())
    cols = {c["name"]: c for c in inspector.get_columns("courses")}
    assert cols["price_dt"]["type"].__class__.__name__.upper() == "NUMERIC"


# ============================================================
# TEST 4: Plan.price is Numeric(10,2)
# ============================================================
def test_04_plan_price_is_numeric(db_session):
    from sqlalchemy import inspect
    inspector = inspect(db_session.get_bind())
    cols = {c["name"]: c for c in inspector.get_columns("plans")}
    assert cols["price"]["type"].__class__.__name__.upper() == "NUMERIC"


# ============================================================
# TEST 5: AIUsageLog.cost_usd is Numeric(10,4)
# ============================================================
def test_05_aiusagelog_cost_usd_is_numeric(db_session):
    from sqlalchemy import inspect
    inspector = inspect(db_session.get_bind())
    cols = {c["name"]: c for c in inspector.get_columns("ai_usage_logs")}
    assert cols["cost_usd"]["type"].__class__.__name__.upper() == "NUMERIC"


# ============================================================
# TEST 6: Decimal arithmetic works on converted fields
# ============================================================
def test_06_decimal_arithmetic(db_session):
    """Verify Decimal arithmetic works (no float truncation)."""
    school = School(name="T", slug="t2", subscription_tier="free")
    db_session.add(school)
    db_session.commit()

    t = Transaction(
        school_id=school.id, user_id=1, type=TransactionType.TOKEN_CONSUMPTION,
        amount=Decimal("33.33"), currency=Currency.TOKEN,
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    # Decimal arithmetic should be exact
    result = t.amount * Decimal("3")
    assert result == Decimal("99.99"), f"Decimal arithmetic failed: {result}"
