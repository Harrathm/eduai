"""Tests for wallet audit trail — credit_balance / debit_balance.

These functions replace direct assignment to User.token_balance / dt_balance.
Every call must produce a WalletTransaction entry (append-only ledger).
"""
import pytest
from app.models import WalletTransaction, WalletPool, User, School, UserRole
from app.services.wallet import credit_balance, debit_balance, get_total_balance, InsufficientCreditsError


def _make_user(db):
    school = School(name="WalletTest", slug="wallet-test", school_type="DEMO")
    db.add(school)
    db.flush()
    user = User(
        email="wallet_audit@test.com", full_name="W",
        role=UserRole.STUDENT, school_id=school.id,
        hashed_password="x", is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def test_credit_balance_creates_wallet_transaction(test_db):
    db, *_ = test_db
    user = _make_user(db)

    tx = credit_balance(
        db, user.id, 50,
        WalletPool.PURCHASED, source="admin", reason="test credit",
    )

    assert tx is not None
    assert tx.amount == 50
    assert tx.pool == WalletPool.PURCHASED
    assert tx.metadata_["source"] == "admin"
    assert tx.metadata_["reason"] == "test credit"
    assert get_total_balance(db, user.id) == 50


def test_credit_balance_append_only(test_db):
    db, *_ = test_db
    user = _make_user(db)

    credit_balance(db, user.id, 30, WalletPool.PURCHASED, source="admin")
    credit_balance(db, user.id, 20, WalletPool.TRIAL, source="admin")
    credit_balance(db, user.id, 10, WalletPool.SCHOOL_ALLOCATED, source="admin")

    tx_count = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user.id
    ).count()
    assert tx_count == 3
    assert get_total_balance(db, user.id) == 60


def test_debit_balance_removes_credits(test_db):
    db, *_ = test_db
    user = _make_user(db)

    credit_balance(db, user.id, 100, WalletPool.PURCHASED, source="admin")
    debit_balance(db, user.id, 40, WalletPool.PURCHASED, source="admin", reason="refund")

    tx_count = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user.id
    ).count()
    assert tx_count == 2  # 1 credit + 1 debit
    assert get_total_balance(db, user.id) == 60


def test_debit_balance_insufficient_raises(test_db):
    db, *_ = test_db
    user = _make_user(db)

    credit_balance(db, user.id, 10, WalletPool.PURCHASED, source="admin")

    with pytest.raises(InsufficientCreditsError):
        debit_balance(db, user.id, 50, WalletPool.PURCHASED, source="admin")


def test_debit_balance_target_pool_only(test_db):
    db, *_ = test_db
    user = _make_user(db)

    credit_balance(db, user.id, 50, WalletPool.PURCHASED, source="admin")
    credit_balance(db, user.id, 30, WalletPool.TRIAL, source="admin")
    debit_balance(db, user.id, 20, WalletPool.PURCHASED, source="admin")

    assert get_total_balance(db, user.id) == 60  # 50-20 + 30
