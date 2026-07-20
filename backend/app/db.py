from __future__ import annotations

import os
import logging
import datetime
from contextvars import ContextVar
from contextlib import contextmanager

from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.orm import with_loader_criteria

logger = logging.getLogger(__name__)

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

# ---------------------------------------------------------------------------
# Multi-tenant context
# ---------------------------------------------------------------------------
# current_tenant_id holds the school_id that should be used to automatically
# filter all SELECT queries on models that define a `school_id` column.
#
# SECURITY: This is the SECOND line of defense for data isolation between
# schools. The first line is check_school_access() in deps.py. This filter
# ensures that even if a developer forgets to call check_school_access() in a
# new endpoint, queries will still only return rows belonging to the current
# user's school.
#
# Global roles (super_admin, pedagogical_admin) bypass this filter via
# tenant_unaware() context manager.
#
# NEVER disable this filter without an explicit security review.
# ---------------------------------------------------------------------------
current_tenant_id: ContextVar[int | None] = ContextVar("current_tenant_id", default=None)

# Per-request flag to suppress tenant filtering for global roles
_tenant_filter_suppressed: ContextVar[bool] = ContextVar("_tenant_filter_suppressed", default=False)


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


@contextmanager
def tenant_unaware():
    """Context manager that suppresses the automatic tenant filter.

    Use this for global roles (super_admin, pedagogical_admin) that have
    legitimate cross-school access. Every usage must be justified in a
    code review.
    """
    token = _tenant_filter_suppressed.set(True)
    try:
        yield
    finally:
        _tenant_filter_suppressed.reset(token)


@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state):
    """Automatically filter SELECT queries by the current tenant (school_id).

    This event fires on every ORM SELECT. It inspects all registered model
    mappers and, for any model that has a `school_id` column, injects an
    additional WHERE clause scoped to the current tenant.

    Bypass conditions:
    - Not a SELECT query (INSERT, UPDATE, DELETE are unaffected)
    - current_tenant_id is None (unauthenticated / pre-auth context)
    - _tenant_filter_suppressed is True (global role context)
    """
    if not execute_state.is_select:
        return
    if _tenant_filter_suppressed.get():
        return
    tenant = current_tenant_id.get()
    if tenant is None:
        return
    # Filter all models that define a school_id column
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, "school_id"):
            execute_state.statement = execute_state.statement.options(
                with_loader_criteria(cls, lambda c: c.school_id == tenant, include_aliases=True)
            )
