import os
import stripe
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from urllib.parse import urlparse
import json

from app.db import get_db
from app.auth import get_current_user
from app.models import User, Subscription, Plan
from app.schemas import SubscriptionRead, SubscriptionCreate, PlanRead

router = APIRouter(tags=["Subscriptions"])


def _is_safe_redirect_url(url: str) -> bool:
    """Validate redirect URL to prevent open redirect attacks.
    Only allows URLs with http/https scheme and no credentials in the netloc.
    Blocks redirects to non-localhost in development.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if parsed.username or parsed.password:
        return False
    # Block redirects to external hosts in production
    env = os.getenv("ENVIRONMENT", "development")
    allowed_hosts = {"localhost", "127.0.0.1", "0.0.0.0"}
    host = parsed.hostname or ""
    if env == "production" and host not in allowed_hosts and not host.endswith(".eduai.platform"):
        return False
    return True


@router.get("/plans", response_model=list[PlanRead])
def list_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).filter(Plan.active == True).order_by(Plan.price).all()
    result = []
    for p in plans:
        features = p.features
        if isinstance(features, str):
            try:
                features = json.loads(features)
            except Exception:
                features = {}
        result.append(PlanRead(
            id=p.id,
            name=p.name,
            stripe_price_id=p.stripe_price_id,
            price=p.price,
            interval=p.interval or "month",
            active=p.active if p.active is not None else True,
            features=features,
        ))
    return result


@router.post("/checkout")
def create_subscription_checkout(
    plan: str = Query(..., description="Plan key: free, pro, school, institution"),
    success_url: str = Query(default="http://localhost:5173/dashboard/subscription?success=1"),
    cancel_url: str = Query(default="http://localhost:5173/dashboard/subscription?cancelled=1"),
    current_user: User = Depends(get_current_user),
):
    try:
        from app.payment.stripe_service import create_checkout_session, PRICES
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe not configured: {str(e)}")

    if plan not in PRICES:
        raise HTTPException(status_code=400, detail="Invalid plan")

    if not _is_safe_redirect_url(success_url) or not _is_safe_redirect_url(cancel_url):
        raise HTTPException(status_code=400, detail="Invalid redirect URL")

    try:
        session = create_checkout_session(
            plan_key=plan,
            school_id=current_user.school_id,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except stripe.error.AuthenticationError:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout: {str(e)}")


@router.get("/current")
def get_current_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(Subscription).filter(
        Subscription.school_id == current_user.school_id,
        Subscription.status == "active",
    ).first()

    if not sub:
        return {"status": "none", "plan": "none", "plan_details": None}

    plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
    features = {}
    if plan and plan.features:
        features = plan.features if isinstance(plan.features, dict) else {}
        try:
            features = json.loads(plan.features)
        except Exception:
            features = {}

    return {
        "id": sub.id,
        "status": sub.status,
        "plan": plan.name if plan else "unknown",
        "plan_key": None,
        "price": plan.price if plan else 0,
        "features": features,
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "ends_at": sub.ends_at.isoformat() if sub.ends_at else None,
        "is_active": sub.is_active if sub.is_active is not None else True,
    }


@router.post("/portal")
def create_portal_session(
    current_user: User = Depends(get_current_user),
):
    try:
        from app.payment.stripe_service import create_customer_portal_session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe not configured: {str(e)}")

    try:
        session = create_customer_portal_session(school_id=current_user.school_id)
        return {"portal_url": session.url}
    except stripe.error.AuthenticationError:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: Optional[str] = Header(None),
):
    from app.payment.stripe_service import construct_webhook_event, PRICES

    payload = await request.body()
    sig = stripe_signature or ""

    try:
        event = construct_webhook_event(payload, sig, WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # Idempotency: check if event was already processed
    event_id = event.get("id")
    if event_id:
        existing_event = db.execute(
            text("SELECT 1 FROM webhook_events WHERE event_id = :eid"),
            {"eid": event_id}
        ).scalar()
        if existing_event:
            return {"received": True, "duplicate": True}

    try:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            plan_key = session.get("metadata", {}).get("plan", "free")
            school_id_str = session.get("metadata", {}).get("school_id")

            if not school_id_str or not school_id_str.isdigit():
                return {"received": True}

            school_id = int(school_id_str)
            price_data = PRICES.get(plan_key, PRICES["basic"])

            plan = db.query(Plan).filter(Plan.name == price_data["name"]).first()
            if not plan:
                plan = Plan(
                    name=price_data["name"],
                    price=price_data["unit_amount"],
                    interval="month",
                    stripe_price_id=price_data.get("stripe_price_id"),
                    active=True,
                )
                db.add(plan)
                db.commit()
                db.refresh(plan)

            existing = db.query(Subscription).filter(
                Subscription.school_id == school_id
            ).first()

            if existing:
                existing.plan_id = plan.id
                existing.status = "active"
                existing.stripe_subscription_id = session.get("subscription") or None
                existing.stripe_customer_id = session.get("customer") or None
                existing.started_at = datetime.now(timezone.utc)
                existing.ends_at = datetime.now(timezone.utc) + timedelta(days=30)
                existing.is_active = True
            else:
                new_sub = Subscription(
                    plan_id=plan.id,
                    school_id=school_id,
                    status="active",
                    stripe_subscription_id=session.get("subscription") or None,
                    stripe_customer_id=session.get("customer") or None,
                    started_at=datetime.now(timezone.utc),
                    ends_at=datetime.now(timezone.utc) + timedelta(days=30),
                    is_active=True,
                )
                db.add(new_sub)

            db.commit()

        elif event["type"] == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            customer_id = invoice.get("customer")
            if customer_id:
                sub = db.query(Subscription).filter(
                    Subscription.stripe_customer_id == customer_id
                ).first()
                if sub:
                    sub.ends_at = datetime.now(timezone.utc) + timedelta(days=30)
                    sub.status = "active"
                    db.commit()

        elif event["type"] == "customer.subscription.deleted":
            sub_data = event["data"]["object"]
            sub_id = sub_data.get("id")
            if sub_id:
                sub = db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == sub_id
                ).first()
                if sub:
                    sub.status = "cancelled"
                    sub.is_active = False
                    db.commit()

        # Record event for idempotency
        if event_id:
            db.execute(
                text("INSERT INTO webhook_events (event_id, event_type, processed_at) VALUES (:eid, :etype, NOW())"),
                {"eid": event_id, "etype": event["type"]}
            )
            db.commit()

        return {"received": True}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/free")
def activate_free_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    free_plan = db.query(Plan).filter(Plan.name == "Free", Plan.active == True).first()
    if not free_plan:
        raise HTTPException(status_code=404, detail="Free plan not found")

    existing = db.query(Subscription).filter(
        Subscription.school_id == current_user.school_id
    ).first()

    if existing:
        existing.plan_id = free_plan.id
        existing.status = "active"
        existing.is_active = True
        existing.started_at = datetime.now(timezone.utc)
        existing.ends_at = None
    else:
        new_sub = Subscription(
            plan_id=free_plan.id,
            school_id=current_user.school_id,
            status="active",
            is_active=True,
            started_at=datetime.now(timezone.utc),
        )
        db.add(new_sub)

    db.commit()
    return {"status": "active", "plan": "Free"}


# ============================================================
# UPGRADE TO INDEPENDENT PAID (State A/C → State C)
# ============================================================

@router.post("/upgrade-to-independent")
def upgrade_to_independent(
    success_url: str = Query(default="http://localhost:5173/dashboard?upgraded=1"),
    cancel_url: str = Query(default="http://localhost:5173/dashboard?cancelled=1"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convert a trial or school-affiliated teacher to an independent paid account.

    Flow:
    1. Creates a Stripe checkout session for the 'independent' plan
    2. On success callback, the webhook (POST /webhook/stripe) finalises:
       - Creates a personal 'individual' school
       - Updates user: school_id, subscription_plan, is_demo_account
    """
    from app.models import SubscriptionPlan

    # Prevent double upgrade
    if current_user.subscription_plan == SubscriptionPlan.INDEPENDENT_PAID:
        raise HTTPException(status_code=400, detail="Account is already independent paid")

    if not _is_safe_redirect_url(success_url) or not _is_safe_redirect_url(cancel_url):
        raise HTTPException(status_code=400, detail="Invalid redirect URL")

    from app.payment.stripe_service import create_checkout_session
    session = create_checkout_session(
        plan_key="independent",
        school_id=current_user.school_id,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": current_user.id, "upgrade_type": "independent"},
    )
    return {"checkout_url": session.url, "session_id": session.id}