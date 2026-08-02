"""
Konnect payment gateway client — Tunisian TND payments.

Konnect API docs: https://docs.konnect.network/

All external HTTP calls are guarded by a circuit breaker to fail fast
when the Konnect API is unreachable.
"""
import hashlib
import hmac
import logging
from typing import Optional

import httpx

from app.core.circuit_breaker import konnect_breaker

logger = logging.getLogger(__name__)

KONNECT_API_BASE = "https://api.konnect.network/api/v1"


class KonnectClient:
    """Lightweight client for the Konnect payment gateway (Tunisia, TND)."""

    def __init__(self, api_key: str, merchant_id: str):
        self.api_key = api_key
        self.merchant_id = merchant_id
        self.base_url = KONNECT_API_BASE

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    @konnect_breaker
    def create_payment(
        self,
        amount_tnd: float,
        order_id: str,
        return_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """Create a payment link via Konnect API.

        Returns dict with at least:
          - pay_url: str   (redirect the user here)
          - pay_id: str    (Konnect payment ID for webhook verification)
        """
        payload = {
            "amount": round(amount_tnd * 1000, 3),  # Konnect expects millimes (1 TND = 1000 millimes)
            "currency": "TND",
            "order_id": order_id,
            "return_url": return_url,
            "cancel_url": cancel_url,
        }
        if customer_email:
            payload["customer_email"] = customer_email
        if customer_name:
            payload["customer_name"] = customer_name
        if description:
            payload["description"] = description

        url = f"{self.base_url}/payments"
        logger.info("Konnect: creating payment %s for order %s", url, order_id)

        resp = httpx.post(url, json=payload, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()

        logger.info("Konnect: payment created pay_id=%s", data.get("pay_id"))
        return data

    @konnect_breaker
    def get_payment(self, pay_id: str) -> dict:
        """Retrieve payment status from Konnect."""
        url = f"{self.base_url}/payments/{pay_id}"
        resp = httpx.get(url, headers=self._headers(), timeout=15)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def verify_webhook_signature(
        payload_body: bytes,
        signature_header: str,
        secret_key: str,
    ) -> bool:
        """Verify Konnect webhook HMAC-SHA256 signature.

        Konnect sends: X-Konnect-Signature header = hex(HMAC-SHA256(secret, body))

        Uses hmac.HMAC (the proper constructor) instead of the deprecated hmac.new().
        Constant-time comparison via hmac.compare_digest prevents timing attacks.
        """
        if not signature_header:
            return False
        mac = hmac.HMAC(
            key=secret_key.encode("utf-8"),
            msg=payload_body,
            digestmod=hashlib.sha256,
        )
        expected = mac.hexdigest()
        return hmac.compare_digest(expected, signature_header)
