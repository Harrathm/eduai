import os
import stripe
from typing import Optional
from datetime import datetime, timedelta


PRICES = {
    "basic": {
        "unit_amount": 0,
        "name": "Basic",
        "stripe_price_id": os.getenv("STRIPE_PRICE_BASIC", "price_basic"),
    },
    "pro": {
        "unit_amount": 500,
        "name": "Teacher Pro",
        "stripe_price_id": os.getenv("STRIPE_PRICE_PRO", "price_pro"),
    },
    "school": {
        "unit_amount": 2900,
        "name": "School",
        "stripe_price_id": os.getenv("STRIPE_PRICE_SCHOOL", "price_school"),
    },
    "institution": {
        "unit_amount": 9900,
        "name": "Institution",
        "stripe_price_id": os.getenv("STRIPE_PRICE_INSTITUTION", "price_institution"),
    },
}


def get_stripe() -> stripe:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    return stripe


def create_checkout_session(
    plan_key: str,
    school_id: int,
    success_url: str = "http://localhost:5173/success",
    cancel_url: str = "http://localhost:5173/pricing",
) -> stripe.CheckoutSession:
    s = get_stripe()

    price_data = PRICES.get(plan_key, PRICES["basic"])

    if price_data["unit_amount"] == 0:
        session = s.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": price_data["name"],
                        },
                        "unit_amount": 0,
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "plan": plan_key,
                "school_id": str(school_id),
            },
            success_url=success_url,
            cancel_url=cancel_url,
        )
    else:
        session = s.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_data["stripe_price_id"],
                    "quantity": 1,
                }
            ],
            metadata={
                "plan": plan_key,
                "school_id": str(school_id),
            },
            subscription_data={
                "metadata": {
                    "plan": plan_key,
                    "school_id": str(school_id),
                }
            },
            success_url=success_url,
            cancel_url=cancel_url,
        )

    return session


def construct_webhook_event(
    payload: bytes,
    sig_header: str,
    endpoint_secret: str,
) -> stripe.Event:
    s = get_stripe()
    return s.Webhook.construct_event(payload, sig_header, endpoint_secret)


def create_customer_portal_session(
    school_id: int,
    return_url: str = "http://localhost:5173/settings",
) -> stripe.BillingPortal.Session:
    s = get_stripe()
    return s.billing_portal.Session.create(
        customer=f"school_{school_id}",
        return_url=return_url,
    )