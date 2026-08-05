"""
Phase 2.2 — Mask email in login logs.

Verifies _mask_email helper masks PII correctly.
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import pytest
from app.auth import _mask_email


def test_01_mask_email_standard():
    """Standard email: j***n@example.com."""
    result = _mask_email("john@example.com")
    assert result == "j***n@example.com"


def test_02_mask_email_short_local():
    """Short local part (<=2 chars): j***@example.com."""
    result = _mask_email("jo@example.com")
    assert result == "j***@example.com"


def test_03_mask_email_single_char():
    """Single char local: j***@example.com."""
    result = _mask_email("j@example.com")
    assert result == "j***@example.com"


def test_04_mask_email_empty():
    """Empty string returns ***."""
    assert _mask_email("") == "***"


def test_05_mask_email_no_at():
    """No @ symbol returns ***."""
    assert _mask_email("notanemail") == "***"


def test_06_mask_email_preserves_domain():
    """Domain should be preserved."""
    result = _mask_email("user@company.co.tn")
    assert result == "u***r@company.co.tn"


def test_07_mask_email_none():
    """None input returns ***."""
    assert _mask_email(None) == "***"
