from __future__ import annotations

import os
import datetime
from contextvars import ContextVar

from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.orm import with_loader_criteria

# Global, shared ORM base and session factory
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Connection pool settings
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    poolclass=pool.QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=True,  # Check connection before checkout
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# Per-request tenant context (school_id)
current_tenant_id: ContextVar[int | None] = ContextVar("current_tenant_id", default=None)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Check database connection health."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state):
    """Automatically filter select queries by the current tenant (school_id).
    Only applies to mapped classes that define a `school_id` column.
    """
    if not execute_state.is_select:
        return
    tenant = current_tenant_id.get()
    if tenant is None:
        return
    # Lazy import to avoid circular dependencies at import time
    try:
        from app.models import TenantMixin  # type: ignore
    except Exception:
        TenantMixin = None  # type: ignore
    if TenantMixin is None:
        return
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, "school_id"):
            execute_state.statement = execute_state.statement.options(
                with_loader_criteria(cls, lambda c: c.school_id == tenant, include_aliases=True)
            )
