"""
Redis-based rate limiter for AI endpoints.
Falls back to in-memory if Redis is unavailable.
"""

import os
import time
import json
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

REDIS_URL = os.getenv("REDIS_URL", "")


class RedisRateLimiter:
    """Per-user rate limiter backed by Redis. Falls back to in-memory dict."""

    def __init__(self):
        self._redis = None
        self._memory_store: dict = {}  # fallback
        self._req_count: int = 0  # counter for periodic cleanup
        if REDIS_URL:
            try:
                import redis
                self._redis = redis.from_url(REDIS_URL, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    def _key(self, user_id: int, endpoint: str) -> str:
        return f"rl:{user_id}:{endpoint}"

    def is_allowed(self, user_id: int, endpoint: str, max_req: int, window: int) -> bool:
        """Check if request is allowed. Returns True if allowed, False if rate limited."""
        if self._redis:
            return self._check_redis(user_id, endpoint, max_req, window)
        return self._check_memory(user_id, endpoint, max_req, window)

    def _check_redis(self, user_id: int, endpoint: str, max_req: int, window: int) -> bool:
        key = self._key(user_id, endpoint)
        pipe = self._redis.pipeline()
        now = time.time()
        window_start = now - window
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = pipe.execute()
        count = results[2]
        return count <= max_req

    def _check_memory(self, user_id: int, endpoint: str, max_req: int, window: int) -> bool:
        key = f"{user_id}:{endpoint}"
        now = time.time()
        self._memory_store[key] = [t for t in self._memory_store.get(key, []) if now - t < window]
        if len(self._memory_store[key]) >= max_req:
            return False
        self._memory_store[key].append(now)
        # Periodic cleanup: purge expired entries every 1000 requests
        self._req_count += 1
        if self._req_count % 1000 == 0:
            self._cleanup_memory(now, window)
        return True

    def _cleanup_memory(self, now: float, default_window: int) -> None:
        """Remove all expired entries from in-memory store."""
        expired_keys = []
        for k, timestamps in self._memory_store.items():
            self._memory_store[k] = [t for t in timestamps if now - t < default_window]
            if not self._memory_store[k]:
                expired_keys.append(k)
        for k in expired_keys:
            del self._memory_store[k]


# Singleton
rate_limiter = RedisRateLimiter()


# AI endpoint rate limits: (max_requests, window_seconds)
AI_RATE_LIMITS = {
    "ai_ask": (30, 60),        # 30 requests/min
    "ai_explain": (20, 60),    # 20 requests/min
    "ai_quiz": (10, 60),       # 10 requests/min
    "ai_generate": (10, 60),   # 10 requests/min
    "ai_ingest": (5, 300),     # 5 requests/5min
    "ai_correct": (20, 60),    # 20 requests/min
}


def check_ai_rate_limit(user_id: int, feature: str) -> None:
    """Check rate limit for AI feature. Raises HTTPException 429 if exceeded."""
    from fastapi import HTTPException
    max_req, window = AI_RATE_LIMITS.get(feature, (30, 60))
    if not rate_limiter.is_allowed(user_id, feature, max_req, window):
        raise HTTPException(
            status_code=429,
            detail=f"Trop de requêtes. Limite: {max_req} appels/{window}s pour {feature}. Réessayez dans quelques instants.",
        )
