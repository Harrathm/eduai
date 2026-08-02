"""
Konnect payment router — checkout + webhook for TND wallet top-ups.

Endpoints:
- POST /konnect/checkout: create a payment link, return pay_url to frontend
- POST /konnect/webhook: receive payment confirmation, credit wallet atomically
"""
import logging
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.deps import set_tenant_context, require_parent
from app.models import User, Transaction, TransactionType, Currency, PaymentStatus
from app.payment.konnect_client import KonnectClient
from app.core.config import get_settings
from app.services.wallet import credit_dt

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Konnect Payments"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class KonnectCheckoutRequest(BaseModel):
    amount_tnd: float  # Amount in TND (e.g. 10.000)
    return_url: str = "http://localhost:5173/wallet"
    cancel_url: str = "http://localhost:5173/wallet"


class KonnectCheckoutResponse(BaseModel):
    pay_url: str
    pay_id: str
    transaction_id: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_konnect_client() -> KonnectClient:
    settings = get_settings()
    if not settings.konnect_api_key or not settings.konnect_merchant_id:
        raise HTTPException(
            status_code=503,
            detail="Konnect n'est pas configuré. Clé API ou merchant ID manquant.",
        )
    return KonnectClient(
        api_key=settings.konnect_api_key,
        merchant_id=settings.konnect_merchant_id,
    )


# ---------------------------------------------------------------------------
# POST /konnect/checkout — create payment link
# ---------------------------------------------------------------------------

@router.post("/konnect/checkout", response_model=KonnectCheckoutResponse)
def konnect_checkout(
    body: KonnectCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Create a Konnect payment link and return it to the frontend.

    Flow:
    1. Create a Transaction (status=pending) for audit trail
    2. Call Konnect API to generate a pay_url
    3. Return pay_url + pay_id + transaction_id to frontend
    """
    if body.amount_tnd <= 0:
        raise HTTPException(status_code=400, detail="Le montant doit être supérieur à 0")
    if body.amount_tnd > 5000:
        raise HTTPException(status_code=400, detail="Montant maximum: 5000 TND")

    # 1. Create pending transaction
    order_id = f"eduai_{current_user.id}_{uuid.uuid4().hex[:12]}"
    transaction = Transaction(
        school_id=current_user.school_id,
        user_id=current_user.id,
        type=TransactionType.DT_DEPOSIT,
        amount=body.amount_tnd,
        currency=Currency.DT,
        description=f"Recharge wallet Konnect ({body.amount_tnd} TND)",
        reference_id=order_id,
        status=PaymentStatus.PENDING.value,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # 2. Call Konnect API
    try:
        konnect = _get_konnect_client()
        result = konnect.create_payment(
            amount_tnd=body.amount_tnd,
            order_id=order_id,
            return_url=body.return_url,
            cancel_url=body.cancel_url,
            customer_email=current_user.email,
            customer_name=current_user.full_name,
            description=f"Recharge wallet EDUAI - {body.amount_tnd} TND",
        )
    except Exception as e:
        logger.error("Konnect checkout failed: %s", e)
        transaction.status = PaymentStatus.FAILED.value
        db.commit()
        raise HTTPException(status_code=502, detail=f"Erreur Konnect: {str(e)}")

    # 3. Store pay_id on the transaction for webhook lookup
    transaction.reference_id = result.get("pay_id", order_id)
    db.commit()

    return KonnectCheckoutResponse(
        pay_url=result.get("pay_url", ""),
        pay_id=result.get("pay_id", ""),
        transaction_id=transaction.id,
    )


# ---------------------------------------------------------------------------
# POST /konnect/webhook — receive payment confirmation
# ---------------------------------------------------------------------------

@router.post("/konnect/webhook")
async def konnect_webhook(request: Request, db: Session = Depends(get_db)):
    """Konnect webhook handler — credits wallet on successful payment.

    Security: verifies HMAC-SHA256 signature before processing.
    Idempotent: checks transaction status before crediting.
    """
    body = await request.body()
    signature = request.headers.get("X-Konnect-Signature", "")

    settings = get_settings()
    if settings.konnect_webhook_secret:
        from app.payment.konnect_client import KonnectClient
        if not KonnectClient.verify_webhook_signature(body, signature, settings.konnect_webhook_secret):
            logger.warning("Konnect webhook: invalid signature")
            raise HTTPException(status_code=403, detail="Signature invalide")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload invalide")

    pay_id = payload.get("pay_id") or payload.get("payment_id")
    status_str = payload.get("status", "")

    if not pay_id:
        raise HTTPException(status_code=400, detail="pay_id manquant")

    # Find the pending transaction
    transaction = db.query(Transaction).filter(
        Transaction.reference_id == pay_id,
        Transaction.status == PaymentStatus.PENDING.value,
    ).first()

    if not transaction:
        # Already processed or unknown — return 200 to avoid retries
        logger.info("Konnect webhook: transaction not found or already processed pay_id=%s", pay_id)
        return {"status": "ignored"}

    # Check payment status from Konnect
    if status_str != "success" and status_str != "completed":
        transaction.status = PaymentStatus.FAILED.value
        db.commit()
        logger.info("Konnect webhook: payment failed pay_id=%s status=%s", pay_id, status_str)
        return {"status": "failed"}

    # Idempotency: credit only once
    amount = Decimal(str(transaction.amount))

    # Credit the user's DT wallet (pool: dt_purchased)
    credit_dt(
        db,
        transaction.user_id,
        amount,
        source="konnect",
        reason=f"Recharge Konnect pay_id={pay_id}",
        commit=False,
    )

    # Mark transaction as succeeded
    transaction.status = PaymentStatus.SUCCEEDED.value
    db.commit()

    logger.info("Konnect webhook: credited %.3f TND to user %s (pay_id=%s)", amount, transaction.user_id, pay_id)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /konnect/credit-child — parent credits child's wallet via Konnect
# ---------------------------------------------------------------------------

class CreditChildRequest(BaseModel):
    amount_tnd: float
    return_url: str = "http://localhost:5173/parent"
    cancel_url: str = "http://localhost:5173/parent"


@router.post("/parents/me/enfants/{eleve_id}/credit-wallet", response_model=KonnectCheckoutResponse)
def credit_child_wallet(
    eleve_id: int,
    body: CreditChildRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    """Parent pays via Konnect to credit their child's DT wallet.

    Flow:
    1. Verify parent ↔ child link
    2. Create pending Transaction for the child
    3. Call Konnect API
    4. Return pay_url to frontend
    """
    from app.models import ParentEnfant

    # Verify parent-child link
    link = db.query(ParentEnfant).filter(
        ParentEnfant.parent_user_id == current_user.id,
        ParentEnfant.eleve_id == eleve_id,
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas lié à cet élève")

    # Verify child exists and is in same school
    child = db.query(User).filter(User.id == eleve_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Élève introuvable")
    if child.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Accès interdit")

    if body.amount_tnd <= 0:
        raise HTTPException(status_code=400, detail="Le montant doit être supérieur à 0")
    if body.amount_tnd > 2000:
        raise HTTPException(status_code=400, detail="Montant maximum: 2000 TND")

    # Create pending transaction (on the child)
    order_id = f"eduai_parent_{current_user.id}_{child.id}_{uuid.uuid4().hex[:10]}"
    transaction = Transaction(
        school_id=current_user.school_id,
        user_id=child.id,  # Credit goes to the child
        type=TransactionType.DT_DEPOSIT,
        amount=body.amount_tnd,
        currency=Currency.DT,
        description=f"Recharge par parent ({body.amount_tnd} TND) → {child.full_name or child.email}",
        reference_id=order_id,
        status=PaymentStatus.PENDING.value,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Call Konnect API
    try:
        konnect = _get_konnect_client()
        result = konnect.create_payment(
            amount_tnd=body.amount_tnd,
            order_id=order_id,
            return_url=body.return_url,
            cancel_url=body.cancel_url,
            customer_email=current_user.email,
            customer_name=current_user.full_name,
            description=f"Recharge wallet enfant {child.full_name or child.email} - {body.amount_tnd} TND",
        )
    except Exception as e:
        logger.error("Konnect checkout for child failed: %s", e)
        transaction.status = PaymentStatus.FAILED.value
        db.commit()
        raise HTTPException(status_code=502, detail=f"Erreur Konnect: {str(e)}")

    transaction.reference_id = result.get("pay_id", order_id)
    db.commit()

    return KonnectCheckoutResponse(
        pay_url=result.get("pay_url", ""),
        pay_id=result.get("pay_id", ""),
        transaction_id=transaction.id,
    )
