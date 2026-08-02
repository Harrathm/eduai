"""
User-facing wallet endpoints: balance, history, purchase.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import Optional
from decimal import Decimal

from app.db import get_db
from app.auth import get_current_user
from app.models import User, WalletTransaction, WalletPool, BillableFeature, Payment, PaymentStatus
from app.services.wallet import get_balance_by_pool, get_total_balance, InsufficientCreditsError

router = APIRouter(tags=["Wallet"])


@router.get("/balance")
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed balance per pool.

    Includes both the modern WalletTransaction ledger AND the legacy
    User.token_balance field (shown as 'legacy' pool) so that existing
    balances are not lost during the migration.
    """
    balances = get_balance_by_pool(db, current_user.id)
    now = datetime.now(timezone.utc)
    result = []

    for pool, amount in balances.items():
        earliest_expiry = (
            db.query(func.min(WalletTransaction.expires_at))
            .filter(
                WalletTransaction.user_id == current_user.id,
                WalletTransaction.pool == pool,
                WalletTransaction.amount > 0,
                WalletTransaction.expires_at != None,
                WalletTransaction.expires_at > now,
            )
            .scalar()
        )
        result.append({
            "pool": pool.value if hasattr(pool, 'value') else str(pool),
            "balance": float(amount),
            "expires_at": earliest_expiry.isoformat() if earliest_expiry else None,
        })

    legacy_tokens = getattr(current_user, "token_balance", 0) or 0
    legacy_dt = getattr(current_user, "dt_balance", 0) or 0
    legacy_total = float(Decimal(str(legacy_tokens)) + Decimal(str(legacy_dt)))

    if legacy_total > 0:
        has_wallet_tx = any(r["balance"] > 0 for r in result)
        if not has_wallet_tx:
            result.append({
                "pool": "legacy",
                "balance": legacy_total,
                "expires_at": None,
            })

    return {
        "user_id": current_user.id,
        "total": float(sum(r["balance"] for r in result)),
        "pools": result,
    }


@router.get("/history")
def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated transaction history."""
    offset = (page - 1) * page_size
    total = db.query(func.count(WalletTransaction.id)).filter(
        WalletTransaction.user_id == current_user.id
    ).scalar()
    txs = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.user_id == current_user.id)
        .order_by(WalletTransaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "transactions": [
            {
                "id": tx.id,
                "pool": tx.pool,
                "amount": tx.amount,
                "feature": tx.feature,
                "expires_at": tx.expires_at.isoformat() if tx.expires_at else None,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in txs
        ],
    }


@router.post("/purchase")
def purchase_credits(
    months: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe checkout for credit purchase (top-up).

    months=1 → 100 credits, months=3 → 350 credits, months=12 → 1500 credits
    """
    import os
    import stripe

    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Payment not configured")

    stripe.api_key = STRIPE_SECRET_KEY

    CREDIT_PACKS = {
        1: {"credits": 100, "amount": 15.00, "label": "100 crédits"},
        3: {"credits": 350, "amount": 39.00, "label": "350 crédits (-14%)"},
        12: {"credits": 1500, "amount": 129.00, "label": "1500 crédits (-29%)"},
    }
    if months not in CREDIT_PACKS:
        raise HTTPException(status_code=400, detail="Invalid pack")

    pack = CREDIT_PACKS[months]

    # Get or create Stripe customer
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            name=current_user.full_name or current_user.email,
            metadata={"user_id": str(current_user.id)},
        )
        current_user.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=current_user.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "tnd",
                "product_data": {"name": f"EDUAI - {pack['label']}"},
                "unit_amount": int(pack["amount"] * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=os.getenv("FRONTEND_URL", "http://localhost:5173") + "/wallet/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=os.getenv("FRONTEND_URL", "http://localhost:5173") + "/wallet/cancel",
        metadata={
            "user_id": str(current_user.id),
            "type": "credit_purchase",
            "credits": str(pack["credits"]),
        },
    )

    # Save payment record
    payment = Payment(
        user_id=current_user.id,
        amount=pack["amount"],
        currency="TND",
        status=PaymentStatus.PENDING,
        stripe_session_id=session.id,
        subscription_months=0,
    )
    db.add(payment)
    db.commit()

    return {"checkout_url": session.url, "session_id": session.id}
