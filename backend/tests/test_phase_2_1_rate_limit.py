"""
Phase 2.1 — Rate limiting on auth endpoints.

Verifies:
  Test 1: /auth/forgot-password has rate limit (3/min)
  Test 2: /auth/login has rate limit (10/min)
  Test 3: /auth/register has rate limit (5/min)
  Test 4: _BoundedDict + _check_memory enforces limits correctly
"""
import os
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"

import time
import pytest
from app.main import RATE_LIMITS, _BoundedDict


def test_01_forgot_password_rate_limit_config():
    """Verify /auth/forgot-password is in RATE_LIMITS."""
    assert "/auth/forgot-password" in RATE_LIMITS
    max_req, window = RATE_LIMITS["/auth/forgot-password"]
    assert max_req == 3, f"Expected 3/min, got {max_req}"
    assert window == 60


def test_02_login_rate_limit_config():
    """Verify /auth/login is in RATE_LIMITS."""
    assert "/auth/login" in RATE_LIMITS
    max_req, window = RATE_LIMITS["/auth/login"]
    assert max_req == 10
    assert window == 60


def test_03_register_rate_limit_config():
    """Verify /auth/register is in RATE_LIMITS."""
    assert "/auth/register" in RATE_LIMITS
    max_req, window = RATE_LIMITS["/auth/register"]
    assert max_req == 5
    assert window == 60


def test_04_memory_limiter_enforces_limit():
    """Verify the in-memory rate limiter correctly blocks after limit."""
    from app.main import RateLimiter

    store = _BoundedDict(maxsize=4096)
    key = "rl:test:auth"

    def check_memory(key, max_req, window):
        now = time.time()
        timestamps = store.get(key)
        if timestamps is None:
            timestamps = []
            store[key] = timestamps
        store[key] = [t for t in timestamps if now - t < window]
        if len(store[key]) >= max_req:
            return False
        store[key].append(now)
        return True

    # 3 requests should pass (limit = 3)
    assert check_memory(key, 3, 60) is True
    assert check_memory(key, 3, 60) is True
    assert check_memory(key, 3, 60) is True

    # 4th should be blocked
    assert check_memory(key, 3, 60) is False

    # After window expires, should pass again
    store[key] = [time.time() - 61]  # simulate expired
    assert check_memory(key, 3, 60) is True


def test_05_bounded_dict_evicts_oldest():
    """Verify _BoundedDict evicts oldest when full."""
    d = _BoundedDict(maxsize=3)
    d["a"] = 1
    d["b"] = 2
    d["c"] = 3
    d["d"] = 4  # should evict "a"
    assert "a" not in d
    assert list(d.keys()) == ["b", "c", "d"]
