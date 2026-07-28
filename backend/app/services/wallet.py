"""
Wallet Service — Multi-pool credit system with append-only ledger.

Design principles:
- Balance is ALWAYS computed at read time (never stored as a mutable field)
- All mutations go through the ledger (INSERT only, no UPDATE/DELETE)
- Consumption order: subscription → school_allocated → trial → purchased
- Cache is avoided in Phase 1 — can be added later if performance requires
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.models import WalletTransaction, WalletPool, BillableFeature


# ---------------------------------------------------------------------------
# Cost estimation (pre-check before AI call)
# ---------------------------------------------------------------------------

# Tokens-per-credit ratio: how many AI tokens equal 1 credit
TOKENS_PER_CREDIT = 500  # 1 credit = 500 tokens consumed

# Per-feature base costs in credits (pessimistic overestimate)
FEATURE_COSTS = {
    BillableFeature.AI_ASK: 2,        # Simple Q&A
    BillableFeature.AI_EXPLAIN: 3,     # Concept explanation (longer)
    BillableFeature.AI_QUIZ: 5,        # Quiz generation
    BillableFeature.AI_GENERATE: 4,    # Exercise generation
    BillableFeature.AI_INGEST: 10,     # PDF ingestion (chunking + embedding)
    BillableFeature.AI_CORRECT: 3,     # Auto-correction
}


def estimate_cost(feature: BillableFeature, input_chars: int = 0) -> int:
    """Return pessimistic estimate of credit cost for a feature.

    Deliberately overestimates to never block an affordable call,
    but also never lets through one that would exceed the balance.
    """
    base = FEATURE_COSTS.get(feature, 2)
    # For text-heavy features, add ~1 credit per 2000 chars input
    if input_chars > 2000:
        base += (input_chars // 2000)
    return base


def tokens_to_credits(input_tokens: int, output_tokens: int) -> int:
    """Convert actual token usage to credit cost (rounded up)."""
    total_tokens = input_tokens + output_tokens
    import math
    return max(1, math.ceil(total_tokens / TOKENS_PER_CREDIT))


# ---------------------------------------------------------------------------
# Balance computation (read-only, no caching in Phase 1)
# ---------------------------------------------------------------------------

class InsufficientCreditsError(Exception):
    """Raised when user has insufficient credits across all pools."""
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(f"Insufficient credits: need {required}, have {available}")


def _now_utc():
    return datetime.now(timezone.utc)


def get_balance_by_pool(db: Session, user_id: int) -> dict[WalletPool, int]:
    """Compute current balance per pool (only non-expired transactions)."""
    now = _now_utc()
    results = (
        db.query(WalletTransaction.pool, func.coalesce(func.sum(WalletTransaction.amount), 0))
        .filter(WalletTransaction.user_id == user_id)
        .filter(
            # For expirable pools, only count non-expired
            (WalletTransaction.pool.in_([WalletPool.PURCHASED, WalletPool.SUBSCRIPTION]))
            |
            ((WalletTransaction.expires_at == None) | (WalletTransaction.expires_at > now))
        )
        .group_by(WalletTransaction.pool)
        .all()
    )
    # Build dict with all pools (default 0)
    balances = {pool: 0 for pool in WalletPool}
    for pool, total in results:
        balances[pool] = max(0, total)  # Never negative
    return balances


def get_total_balance(db: Session, user_id: int) -> int:
    """Compute total balance across all pools (non-expired only)."""
    balances = get_balance_by_pool(db, user_id)
    return sum(balances.values())


# ---------------------------------------------------------------------------
# Credit consumption (strict priority order)
# ---------------------------------------------------------------------------

def consume_credits(
    db: Session,
    user_id: int,
    amount: int,
    feature: BillableFeature,
    related_request_id: Optional[str] = None,
) -> list[dict]:
    """Consume credits following strict priority order.

    Priority: subscription → school_allocated → trial → purchased
    (consume most perishable first, save purchased — never expires — for last)

    Returns list of debits actually applied (one per pool touched).
    Raises InsufficientCreditsError if total balance < amount.
    """
    from sqlalchemy import select

    # Use SELECT FOR UPDATE to lock rows and prevent race conditions
    stmt = (
        select(WalletTransaction)
        .where(WalletTransaction.user_id == user_id)
        .with_for_update()
    )
    db.execute(stmt)

    total = get_total_balance(db, user_id)
    if total < amount:
        raise InsufficientCreditsError(required=amount, available=total)

    # Priority order (most perishable first)
    consumption_order = [
        WalletPool.SUBSCRIPTION,      # Resets each billing cycle
        WalletPool.SCHOOL_ALLOCATED,  # Expires at contract end
        WalletPool.TRIAL,             # Expires after N days
        WalletPool.PURCHASED,         # Never expires — save for last
    ]

    balances = get_balance_by_pool(db, user_id)
    remaining = amount
    debits = []

    for pool in consumption_order:
        if remaining <= 0:
            break
        pool_balance = balances.get(pool, 0)
        if pool_balance <= 0:
            continue

        debit_amount = min(pool_balance, remaining)
        tx = WalletTransaction(
            user_id=user_id,
            pool=pool,
            amount=-debit_amount,  # Negative = debit
            feature=feature,
            related_request_id=related_request_id,
        )
        db.add(tx)
        remaining -= debit_amount
        debits.append({"pool": pool, "amount": debit_amount})

    db.commit()

    # Check low balance after consumption
    alert = check_low_balance_alert(db, user_id)

    return debits


def add_credits(
    db: Session,
    user_id: int,
    pool: WalletPool,
    amount: int,
    expires_at: Optional[datetime] = None,
    metadata: Optional[dict] = None,
) -> WalletTransaction:
    """Add credits to a specific pool. Called by auth/subscription/purchase flows."""
    tx = WalletTransaction(
        user_id=user_id,
        pool=pool,
        amount=amount,  # Positive = credit
        expires_at=expires_at,
        metadata_=metadata,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


# ---------------------------------------------------------------------------
# Admin credit / debit (append-only, replaces direct assignment)
# ---------------------------------------------------------------------------

def credit_balance(
    db: Session,
    user_id: int,
    amount: int,
    pool: WalletPool = WalletPool.PURCHASED,
    source: str = "admin",
    reason: str = "",
    expires_at: Optional[datetime] = None,
) -> WalletTransaction:
    """Add credits via a WalletTransaction (append-only, no direct field mutation).

    This is the ONLY sanctioned way for admin endpoints to adjust user balances.
    Every call produces a ledger entry with full traceability.
    """
    meta = {"source": source, "reason": reason}
    if expires_at:
        meta["expires_at"] = expires_at.isoformat()
    tx = WalletTransaction(
        user_id=user_id,
        pool=pool,
        amount=max(0, amount),
        expires_at=expires_at,
        metadata_=meta,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def debit_balance(
    db: Session,
    user_id: int,
    amount: int,
    pool: WalletPool = WalletPool.PURCHASED,
    source: str = "admin",
    reason: str = "",
) -> WalletTransaction:
    """Remove credits via a WalletTransaction (append-only, no direct field mutation).

    Raises InsufficientCreditsError if pool balance < amount.
    """
    balances = get_balance_by_pool(db, user_id)
    pool_balance = balances.get(pool, 0)
    if pool_balance < amount:
        raise InsufficientCreditsError(required=amount, available=pool_balance)
    tx = WalletTransaction(
        user_id=user_id,
        pool=pool,
        amount=-amount,
        metadata_={"source": source, "reason": reason},
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


# ---------------------------------------------------------------------------
# Low balance alerts
# ---------------------------------------------------------------------------

# Reference balance = sum of all credits ever granted (lifetime)
# Alert thresholds: 20% and 10% of reference

def _get_reference_balance(db: Session, user_id: int) -> int:
    """Compute reference balance (total credits ever granted, non-expired)."""
    now = _now_utc()
    total = (
        db.query(func.coalesce(func.sum(WalletTransaction.amount), 0))
        .filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.amount > 0,
            (WalletTransaction.expires_at == None) | (WalletTransaction.expires_at > now),
        )
        .scalar()
    )
    return max(1, total)  # Avoid division by zero


def check_low_balance_alert(db: Session, user_id: int) -> Optional[dict]:
    """Check if balance is below threshold and return alert info.

    Returns None if no alert needed, or dict with alert details.
    Caller should send notification based on the returned dict.
    """
    total = get_total_balance(db, user_id)
    reference = _get_reference_balance(db, user_id)
    pct = (total / reference) * 100

    # Check if user already has a pending alert at this threshold
    from app.models import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    # Determine threshold
    if pct <= 10:
        threshold = "critical"
        pct_label = "10%"
    elif pct <= 20:
        threshold = "warning"
        pct_label = "20%"
    else:
        return None

    # Check if this alert was already sent (avoid re-notifying)
    existing = (
        db.query(WalletTransaction)
        .filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.pool == WalletPool.TRIAL,  # Use trial pool as metadata store
            WalletTransaction.metadata_["alert_type"].as_string() == f"low_balance_{threshold}",
        )
        .first()
    )
    if existing:
        return None

    # Record the alert to avoid re-notifying
    alert_tx = WalletTransaction(
        user_id=user_id,
        pool=WalletPool.TRIAL,  # Dummy — no balance change
        amount=0,
        metadata_={"alert_type": f"low_balance_{threshold}", "balance": total, "pct": pct},
    )
    db.add(alert_tx)
    db.commit()

    # Build message based on user role
    role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role == "student":
        message = f"Solde faible ({pct_label}). Contactez votre école pour plus de crédits."
        cta = None
    elif role in ("teacher", "admin_school", "pedagogical_lead"):
        message = f"Solde faible ({pct_label}). Rechargez votre portefeuille."
        cta = "/wallet/purchase"
    else:
        message = f"Solde faible ({pct_label})."
        cta = None

    return {
        "threshold": threshold,
        "message": message,
        "cta": cta,
        "balance": total,
        "reference": reference,
        "percentage": round(pct, 1),
    }
