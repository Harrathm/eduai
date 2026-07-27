from __future__ import annotations

import os
import uuid
import json
import time
import logging
import sys
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
from app.models_lms import LmsBase
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
from app.routers.wallet import router as wallet_router
from app.routers.conversations import router as conversations_router
from app.routers.pedagogical import router as pedagogical_router
from app.routers.pedagogical_lead import router as pedagogical_lead_router
from app.routers.packs import router as packs_router
from app.routers.inbox import router as inbox_router
from app.routers.placement import router as placement_router
from app.routers.goals import learner_router as goals_learner_router
from app.routers.goals import pedagogical_lead_router as goals_pedagogical_router

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


class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, rates: dict):
        super().__init__(app)
        self.rates = rates

    async def dispatch(self, request: Request, call_next):
        # Only bypass rate limiting when explicitly in test mode (not production)
        if TESTING and os.environ.get("ENVIRONMENT", "development") != "production":
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        for path_pattern, (max_req, window) in self.rates.items():
            if request.url.path.startswith(path_pattern):
                key = f"{client_ip}:{path_pattern}"
                now = time.time()
                self.requests[key] = [t for t in self.requests.get(key, []) if now - t < window]
                if len(self.requests[key]) >= max_req:
                    return JSONResponse(status_code=429, content={"error": "rate_limit_exceeded"})
                self.requests[key].append(now)
                break
        return await call_next(request)

    requests: dict = {}


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting EDUAI Learning Backend...")
    Base.metadata.create_all(bind=engine)
    LmsBase.metadata.create_all(bind=engine)
    logger.info("Database tables created")

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
    """Block non-admin requests when maintenance mode is enabled."""
    path = request.url.path
    if path.startswith("/api/admin/") or path in ("/", "/health", "/docs", "/openapi.json"):
        return await call_next(request)

    try:
        from app.db import SessionLocal
        db = SessionLocal()
        from app.models import PlatformSettings
        setting = db.query(PlatformSettings).filter(
            PlatformSettings.key == "maintenance_mode",
            PlatformSettings.school_id == None,
        ).first()
        db.close()
        if setting and setting.value and setting.value.lower() in ("true", "1", "yes"):
            from fastapi.responses import JSONResponse
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
    except Exception:
        pass
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
app.include_router(wallet_router, prefix="/api/wallet")
app.include_router(conversations_router)
app.include_router(pedagogical_router, prefix="/api")
app.include_router(pedagogical_lead_router, prefix="/api")
app.include_router(packs_router, prefix="/api")
app.include_router(inbox_router, prefix="/api")
app.include_router(placement_router, prefix="/api")
app.include_router(goals_learner_router, prefix="/api")
app.include_router(goals_pedagogical_router, prefix="/api")


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