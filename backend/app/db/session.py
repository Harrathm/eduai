"""Database session configuration — with multi-tenant filtering.

SECURITY: This module implements automatic school-level data isolation via a
SQLAlchemy session event. Every SELECT query on models with a `school_id` column
is automatically filtered by the current tenant.

NEVER disable the tenant filter without an explicit security review.
"""
import os
import logging
from contextvars import ContextVar
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, with_loader_criteria

logger = logging.getLogger(__name__)

from app.core.config import get_settings
settings = get_settings()

# Use DATABASE_URL from settings
db_url = settings.database_url if settings.database_url else "sqlite:///./eduai.db"

# Use Base from models.py so all models share the same metadata
from app.models import Base


engine = create_engine(db_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import all models to register them with Base.metadata
from app.models import (
    School, User, Course, Module, Lesson, Assignment, Submission,
    Transaction, TokenPackage, CourseEnrollment, ClassroomEnrollment,
    CoursePurchase, StudyPack, PackPurchase, Document, Message, PlatformSetting, TeacherRegistration,
    UserRole, SubscriptionTier, EnrollmentStatus, TransactionType, Currency,
    ContentType, CourseStatus, NiveauScolaire, PackStatus, PackPurchaseStatus, PurchaserType,
    DocumentStatus, TeacherRegistrationStatus, MessageType,
    Progress,
    NiveauEtude, Matiere, ChapterPathway, Notion, ContenuNotion,
    ProfilAssimilationEleve, HistoriqueScoreEleve, NotificationReorientation,
    NiveauAssimilation, TypeContenu, StatutContenuPedagogique, SourceChangement,
    StatutValidationProfil, ActionReorientation,
)


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
# _tenant_filter_suppressed.
#
# NEVER disable this filter without an explicit security review.
# ---------------------------------------------------------------------------
current_tenant_id: ContextVar[int | None] = ContextVar("current_tenant_id", default=None)
_tenant_filter_suppressed: ContextVar[bool] = ContextVar("_tenant_filter_suppressed", default=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


__all__ = ["engine", "SessionLocal", "Base", "get_db", "current_tenant_id",
           "_tenant_filter_suppressed", "tenant_unaware"]