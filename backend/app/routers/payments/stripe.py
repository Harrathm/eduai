"""
Stripe Payment Integration for Independent Teacher Subscriptions
Handles checkout, webhooks, and subscription lifecycle.
"""

import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.db import get_db
from app.auth import get_current_user
from app.models import User, Payment, PaymentStatus, UserRole
from app.audit import log_admin_action

router = APIRouter(tags=["Payments"])

# Stripe config
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")  # Monthly price ID

# Pricing (TND)
PRICING = {
    1: {"amount": 29.00, "label": "1 mois"},
    3: {"amount": 79.00, "label": "3 mois (-8%)"},
    12: {"amount": 299.00, "label": "12 ans (-14%)"},
}

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


def _get_or_create_stripe_customer(user: User) -> str:
    """Get or create a Stripe customer for a user."""
    if user.stripe_customer_id:
        return user.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=user.full_name or user.email,
        metadata={"user_id": str(user.id)},
    )
    user.stripe_customer_id = customer.id
    return customer.id


@router.post("/checkout")
def create_checkout_session(
    months: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe Checkout Session for subscription payment."""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can subscribe")
    if getattr(current_user, "subscription_plan", None) == "independent_paid":
        expires = getattr(current_user, "subscription_expires_at", None)
        if expires and expires > datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Subscription already active")

    if months not in PRICING:
        raise HTTPException(status_code=400, detail="Invalid subscription duration")

    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    customer_id = _get_or_create_stripe_customer(current_user)
    pricing = PRICING[months]

    # Create Stripe Checkout Session
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "tnd",
                "product_data": {
                    "name": f"EDUAI Independent - {pricing['label']}",
                    "description": "Accès complet plateforme enseignant indépendant",
                },
                "unit_amount": int(pricing["amount"] * 100),  # Stripe uses cents
                "recurring": None,  # One-time payment, manual renewal
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=os.getenv("FRONTEND_URL", "http://localhost:5173") + "/subscription/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=os.getenv("FRONTEND_URL", "http://localhost:5173") + "/subscription/cancel",
        metadata={
            "user_id": str(current_user.id),
            "months": str(months),
        },
    )

    # Save payment record
    payment = Payment(
        user_id=current_user.id,
        amount=pricing["amount"],
        currency="TND",
        status=PaymentStatus.PENDING,
        stripe_session_id=session.id,
        subscription_months=months,
    )
    db.add(payment)
    db.commit()

    log_admin_action(db, current_user.id, current_user.email or "unknown",
              "payment.checkout_created",
              target_type="user", target_id=current_user.id,
              details=f"Checkout session created: {months} months, {pricing['amount']} TND")

    return {"checkout_url": session.url, "session_id": session.id}


@router.get("/status")
def get_payment_status(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check payment status after checkout."""
    payment = db.query(Payment).filter(
        Payment.stripe_session_id == session_id,
        Payment.user_id == current_user.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {
        "status": payment.status,
        "amount": payment.amount,
        "currency": payment.currency,
        "months": payment.subscription_months,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
    }


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Stripe webhook not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        _handle_checkout_completed(session, db)
    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        _handle_payment_failed(intent, db)

    return {"ok": True}


def _handle_checkout_completed(session: dict, db: Session):
    """Activate subscription after successful payment."""
    user_id = int(session["metadata"]["user_id"])
    months = int(session["metadata"]["months"])

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return

    payment = db.query(Payment).filter(
        Payment.stripe_session_id == session["id"]
    ).first()
    if payment:
        payment.status = PaymentStatus.SUCCEEDED
        payment.stripe_payment_intent = session.get("payment_intent")

    # Activate subscription
    now = datetime.now(timezone.utc)
    current_expiry = getattr(user, "subscription_expires_at", None)
    if current_expiry and current_expiry > now:
        user.subscription_expires_at = current_expiry + timedelta(days=months * 30)
    else:
        user.subscription_expires_at = now + timedelta(days=months * 30)

    user.subscription_plan = "independent_paid"
    db.commit()

    # Grant subscription credits based on plan
    from app.services.wallet import add_credits
    from app.models import WalletPool
    CREDITS_PER_MONTH = 200  # 200 credits per month of subscription
    total_credits = months * CREDITS_PER_MONTH
    add_credits(
        db, user_id, WalletPool.SUBSCRIPTION, total_credits,
        expires_at=user.subscription_expires_at,
        metadata={"subscription_months": months, "payment_id": payment.id if payment else None},
    )

    log_admin_action(db, user_id, user.email or "unknown",
              "payment.subscription_activated",
              target_type="user", target_id=user_id,
              details=f"Activated {months} months, {total_credits} credits, expires {user.subscription_expires_at}")


def _handle_payment_failed(intent: dict, db: Session):
    """Handle failed payment."""
    payment = db.query(Payment).filter(
        Payment.stripe_payment_intent == intent["id"]
    ).first()
    if payment:
        payment.status = PaymentStatus.FAILED
        db.commit()

    log_admin_action(db, 0, "system", "payment.failed",
              target_type="payment", target_id=payment.id if payment else 0,
              details=f"Payment intent failed: {intent['id']}")
