from __future__ import annotations

import os
import uuid
import json
import time
import logging
import sys
from collections import OrderedDict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import text
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles

from app.db import engine, Base, current_tenant_id
from app.core.config import get_settings

TESTING = os.environ.get("TESTING", "").lower() == "true"
from app.auth import router as auth_router
from app.routers.lms import router as lms_router
from app.routers.academy import router as academy_router
from app.routers.ai import router as ai_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.admin import router as admin_router
from app.routers.users import router as users_router
from app.routers.courses import router as courses_router
from app.routers.admin_chapters import router as admin_chapters_router
from app.routers.admin_lessons import router as admin_lessons_router
from app.routers.admin_quizzes import router as admin_quizzes_router
from app.routers.learner import router as learner_router
from app.routers.admin_courses import router as admin_courses_router
from app.routers.catalog import router as catalog_router
from app.routers.media import router as media_router
from app.routers.ai_factory import router as ai_factory_router
from app.routers.logs import router as logs_router
from app.routers.teacher_classes import teacher_router, admin_teacher_router
from app.routers.payments.stripe import router as payments_router
from app.routers.payments.konnect import router as konnect_router
from app.routers.wallet import router as wallet_router
from app.routers.conversations import router as conversations_router
from app.routers.pedagogical import router as pedagogical_router
from app.routers.pedagogical_lead import router as pedagogical_lead_router
from app.routers.packs import router as packs_router
from app.routers.inbox import router as inbox_router
from app.routers.placement import router as placement_router
from app.routers.goals import learner_router as goals_learner_router
from app.routers.goals import pedagogical_lead_router as goals_pedagogical_router
from app.routers.adaptive_pathway import router as adaptive_pathway_router
from app.routers.gamification import router as gamification_router
from app.routers.parent import router as parent_router

# Import models_lms to register its models with Base metadata
import app.models_lms


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        return json.dumps(log_obj)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Rate Limiter — Redis-backed with in-memory fallback
# ---------------------------------------------------------------------------

class RateLimiter(BaseHTTPMiddleware):
    """IP-based rate limiter for path-prefix rules.

    Uses Redis for distributed rate limiting when REDIS_URL is set.
    Falls back to an in-memory bounded dict for local development.
    """

    _MEMORY_MAX_KEYS = 4096

    def __init__(self, app, rates: dict):
        super().__init__(app)
        self.rates = rates
        self._redis = None
        self._memory_store: _BoundedDict = _BoundedDict(maxsize=self._MEMORY_MAX_KEYS)
        self._backend = "memory"

        redis_url = os.getenv("REDIS_URL", "")
        if redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(redis_url, decode_responses=True)
                self._backend = "redis"
                logger.info("RateLimiter: using Redis backend (%s)", redis_url.split("@")[-1])
            except Exception as exc:
                logger.warning("RateLimiter: Redis unavailable, falling back to memory — %s", exc)

    async def dispatch(self, request: Request, call_next):
        if TESTING and os.environ.get("ENVIRONMENT", "development") != "production":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        for path_pattern, (max_req, window) in self.rates.items():
            if request.url.path.startswith(path_pattern):
                key = f"rl:{client_ip}:{path_pattern}"
                try:
                    allowed = await self._check(key, max_req, window)
                except Exception:
                    # If Redis dies mid-request, don't block the user
                    allowed = True
                if not allowed:
                    return JSONResponse(status_code=429, content={"error": "rate_limit_exceeded"})
                break

        return await call_next(request)

    # -- Redis path (async) -------------------------------------------------

    async def _check(self, key: str, max_req: int, window: int) -> bool:
        if self._redis and self._backend == "redis":
            return await self._check_redis(key, max_req, window)
        return self._check_memory(key, max_req, window)

    async def _check_redis(self, key: str, max_req: int, window: int) -> bool:
        pipe = self._redis.pipeline()
        now = time.time()
        window_start = now - window
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        count = results[2]
        return count <= max_req

    # -- Memory fallback (sync, bounded) ------------------------------------

    def _check_memory(self, key: str, max_req: int, window: int) -> bool:
        now = time.time()
        timestamps = self._memory_store.get(key)
        if timestamps is None:
            timestamps = []
            self._memory_store[key] = timestamps
        # Prune expired
        self._memory_store[key] = [t for t in timestamps if now - t < window]
        if len(self._memory_store[key]) >= max_req:
            return False
        self._memory_store[key].append(now)
        return True


class _BoundedDict(OrderedDict):
    """Dict with a hard max size; evicts oldest entries when full."""

    def __init__(self, maxsize: int = 4096):
        super().__init__()
        self._maxsize = maxsize

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        elif len(self) >= self._maxsize:
            self.popitem(last=False)
        super().__setitem__(key, value)


RATE_LIMITS = {
    "/auth/login": (10, 60),
    "/auth/register": (5, 60),
    "/auth/register-trial-teacher": (5, 60),
    "/api/ai/": (60, 60),
    "/api/admin/": (200, 60),
    "/api/wallet/": (30, 60),
    "/api/subscriptions/checkout": (5, 60),
}


_default_origins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",")
    if o.strip()
]


# ---------------------------------------------------------------------------
# Maintenance mode — cached check (TTL 60 s)
# ---------------------------------------------------------------------------

_MAINTENANCE_TTL = 60  # seconds
_maintenance_cache: dict[str, tuple[bool, float]] = {}


def _is_maintenance_mode() -> bool:
    """Return True if global maintenance mode is ON, with a 60 s in-memory cache."""
    now = time.time()
    cached = _maintenance_cache.get("global")
    if cached:
        value, ts = cached
        if now - ts < _MAINTENANCE_TTL:
            return value

    try:
        from app.db import SessionLocal
        from app.models import PlatformSettings
        db = SessionLocal()
        setting = db.query(PlatformSettings).filter(
            PlatformSettings.key == "maintenance_mode",
            PlatformSettings.school_id == None,
        ).first()
        db.close()

        value = bool(setting and setting.value and setting.value.lower() in ("true", "1", "yes"))
    except Exception:
        value = False

    _maintenance_cache["global"] = (value, now)
    return value


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting EDUAI Learning Backend...")

    # Démarrer le scheduler d'expiration des packs
    from app.services.course_access import start_pack_expiration_scheduler
    start_pack_expiration_scheduler()

    # Démarrer le scheduler de génération d'objectifs
    from app.services.goal_scheduler import start_goal_scheduler
    start_goal_scheduler()

    yield
    logger.info("Shutting down...")


environment = os.environ.get("ENVIRONMENT", "development")

app = FastAPI(
    title="EDUAI Learning API",
    description="Multi-tenant SaaS EdTech Platform API",
    version="1.0.0",
    docs_url="/docs" if environment != "production" else None,
    redoc_url="/redoc" if environment != "production" else None,
    openapi_url="/openapi.json" if environment != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(RateLimiter, rates=RATE_LIMITS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-Tenant-ID"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.middleware("http")
async def maintenance_mode_middleware(request: Request, call_next):
    """Block non-admin requests when maintenance mode is enabled.

    The maintenance flag is cached in-memory for 60 s to avoid a DB round-trip
    on every single request.  The cache is process-local (fine for single-worker
    dev; in multi-worker prod the worst case is a 60 s propagation delay).
    """
    path = request.url.path
    if path.startswith("/api/admin/") or path in ("/", "/health", "/docs", "/openapi.json"):
        return await call_next(request)

    if _is_maintenance_mode():
        origin = request.headers.get("origin", "")
        headers = {}
        if origin in ALLOWED_ORIGINS:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Allow-Methods"] = "*"
            headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, X-Tenant-ID"
        return JSONResponse(
            status_code=503,
            content={
                "error": "maintenance_mode",
                "message": "Platform is under maintenance. Please check back later.",
            },
            headers=headers,
        )

    return await call_next(request)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    logger.info(f"-> {request.method} {request.url.path}", extra={
        "request_id": request_id, "method": request.method,
        "path": request.url.path, "client_ip": client_ip,
    })

    try:
        response = await call_next(request)
        logger.info(f"<- {request.method} {request.url.path} - {response.status_code}", extra={
            "request_id": request_id, "status_code": response.status_code,
        })
    except Exception as e:
        logger.error(f"ERROR {request.method} {request.url.path}: {str(e)}", extra={
            "request_id": request_id, "error": str(e)}, exc_info=True)
        raise

    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    is_dev = settings.environment == "development"
    error_detail = {
        "error": "internal_server_error",
        "message": "An unexpected error occurred" if settings.is_production else str(exc),
        "request_id": request_id,
    }
    if is_dev:
        error_detail["detail"] = str(exc)
        error_detail["type"] = type(exc).__name__

    origin = request.headers.get("origin", "")
    headers = {"X-Request-ID": request_id}
    if origin in ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"

    return JSONResponse(status_code=500, content=error_detail, headers=headers)


app.include_router(auth_router, prefix="/auth")
app.include_router(lms_router, prefix="/api/lms")
app.include_router(academy_router, prefix="/api/academy")
app.include_router(ai_router, prefix="/api/ai")
app.include_router(subscriptions_router, prefix="/api/subscriptions")
app.include_router(admin_chapters_router, prefix="/api/admin/chapters")
app.include_router(admin_lessons_router, prefix="/api/admin/lessons")
app.include_router(admin_quizzes_router, prefix="/api/admin/quizzes")
app.include_router(admin_router, prefix="/api/admin")
app.include_router(admin_courses_router, prefix="/api/admin/courses")
app.include_router(catalog_router, prefix="/catalog")
app.include_router(media_router, prefix="/api/admin/media")
app.include_router(learner_router, prefix="/api/learner")
app.include_router(users_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(ai_factory_router)
app.include_router(logs_router)
app.include_router(teacher_router, prefix="/api/teacher")
app.include_router(admin_teacher_router, prefix="/api/admin")
app.include_router(payments_router, prefix="/api/payments")
app.include_router(konnect_router, prefix="/api")
app.include_router(wallet_router, prefix="/api/wallet")
app.include_router(conversations_router)
app.include_router(pedagogical_router, prefix="/api")
app.include_router(pedagogical_lead_router, prefix="/api")
app.include_router(packs_router, prefix="/api")
app.include_router(inbox_router, prefix="/api")
app.include_router(placement_router, prefix="/api")
app.include_router(goals_learner_router, prefix="/api")
app.include_router(goals_pedagogical_router, prefix="/api")
app.include_router(adaptive_pathway_router, prefix="/api/pathway")
app.include_router(gamification_router, prefix="/api/gamification")
app.include_router(parent_router, prefix="/api")


# Add file logging for error log viewer
import os
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "backend.log")
file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
file_handler.setFormatter(JSONFormatter())
file_handler.setLevel(logging.WARNING)
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
logger.info(f"File logging enabled: {log_file}")


@app.get("/")
async def root():
    return {"name": "EDUAI Learning API", "version": "1.0.0", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "version": "1.0.0"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})
