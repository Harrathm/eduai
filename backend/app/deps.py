from typing import Optional

from fastapi import Depends, HTTPException, status
from app.auth import get_current_user
from app.models import User
from app.db import current_tenant_id, _tenant_filter_suppressed


# ---------------------------------------------------------------------------
# Tenant context setup
# ---------------------------------------------------------------------------

def set_tenant_context(current_user: User = Depends(get_current_user)) -> User:
    """Populate the multi-tenant context for automatic DB-level filtering.

    This dependency MUST be added (directly or via a wrapper like require_admin)
    to every endpoint that queries school-scoped models. It sets:
    - current_tenant_id = user's school_id (for scoped roles)
    - suppresses filtering for global roles (super_admin, pedagogical_admin)

    SECURITY: This is the second line of defense for school data isolation.
    The first line is check_school_access(). Never remove this dependency.
    """
    role = get_user_role(current_user)
    if role in ("super_admin", "pedagogical_admin"):
        # Global roles legitimately access all schools — suppress tenant filter
        _tenant_filter_suppressed.set(True)
    else:
        # Scoped roles: set tenant to their school
        school_id = getattr(current_user, "school_id", None)
        if school_id is not None:
            current_tenant_id.set(school_id)
    return current_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_user_role(user: User) -> str:
    """Extract the effective role string from a User.

    Priority: active_context_role > role column.
    This ensures the RBAC system uses the context-switched role when available,
    while falling back to the primary role for backward compatibility.
    """
    # Prefer active_context_role (set by context switcher or JWT claim)
    if user.active_context_role:
        return str(user.active_context_role).lower()
    raw = user.role
    return str(raw.value).lower() if hasattr(raw, "value") else str(raw).lower().replace("userrole.", "")


# ---------------------------------------------------------------------------
# Permission dependencies — General
# ---------------------------------------------------------------------------

def require_admin(current_user: User = Depends(set_tenant_context)) -> User:
    """Require SUPER_ADMIN, ADMIN_SCHOOL, PEDAGOGICAL_ADMIN or PEDAGOGICAL_LEAD role.

    Also sets the multi-tenant context for automatic DB-level school filtering.
    """
    role = get_user_role(current_user)
    if role not in ("super_admin", "admin_school", "pedagogical_admin", "pedagogical_lead"):
        raise HTTPException(status_code=403, detail=f"Admin access required. Role='{role}'")
    return current_user


# Alias for clarity in new code
require_any_admin = require_admin


def require_platform_admin(current_user: User = Depends(set_tenant_context)) -> User:
    """Require SUPER_ADMIN or PEDAGOGICAL_ADMIN role (platform-level, no school scope)."""
    role = get_user_role(current_user)
    if role not in ("super_admin", "pedagogical_admin"):
        raise HTTPException(status_code=403, detail="Platform admin access required")
    return current_user


def require_school_admin(current_user: User = Depends(set_tenant_context)) -> User:
    """Require ADMIN_SCHOOL or PEDAGOGICAL_LEAD role (school-scoped)."""
    role = get_user_role(current_user)
    if role not in ("admin_school", "pedagogical_lead"):
        raise HTTPException(status_code=403, detail="School admin access required")
    if not getattr(current_user, "school_id", None):
        raise HTTPException(status_code=403, detail="School admin must be assigned to a school")
    return current_user


def require_school_admin_strict(current_user: User = Depends(set_tenant_context)) -> User:
    """Require ADMIN_SCHOOL role ONLY — for administrative/commercial actions
    (pack purchases, student imports) that pedagogical_lead must NOT perform."""
    role = get_user_role(current_user)
    if role != "admin_school":
        raise HTTPException(status_code=403, detail="School admin (strict) access required")
    if not getattr(current_user, "school_id", None):
        raise HTTPException(status_code=403, detail="School admin must be assigned to a school")
    return current_user


def require_super_admin(current_user: User = Depends(set_tenant_context)) -> User:
    """Require SUPER_ADMIN role only. Also sets tenant context."""
    if get_user_role(current_user) != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


def require_teacher_or_admin(current_user: User = Depends(set_tenant_context)) -> User:
    """Require TEACHER, ADMIN_SCHOOL, or SUPER_ADMIN role. Also sets tenant context."""
    role = get_user_role(current_user)
    if role not in ("super_admin", "admin_school", "teacher"):
        raise HTTPException(status_code=403, detail=f"Teacher or admin access required. Role='{role}'")
    return current_user


# ---------------------------------------------------------------------------
# Permission dependencies — Pedagogical roles
# ---------------------------------------------------------------------------

def require_pedagogical_admin(current_user: User = Depends(set_tenant_context)) -> User:
    """Require PEDAGOGICAL_ADMIN role (platform-wide). Also sets tenant context."""
    if get_user_role(current_user) != "pedagogical_admin":
        raise HTTPException(status_code=403, detail="Pedagogical admin (platform) access required")
    return current_user


def require_pedagogical_lead(current_user: User = Depends(set_tenant_context)) -> User:
    """Require PEDAGOGICAL_LEAD role (school-scoped). Also sets tenant context."""
    if get_user_role(current_user) != "pedagogical_lead":
        raise HTTPException(status_code=403, detail="Pedagogical lead (school) access required")
    if not getattr(current_user, "school_id", None):
        raise HTTPException(status_code=403, detail="Pedagogical lead must be assigned to a school")
    return current_user


def require_pedagogical_any(current_user: User = Depends(set_tenant_context)) -> User:
    """Require either PEDAGOGICAL_ADMIN or PEDAGOGICAL_LEAD role. Also sets tenant context."""
    role = get_user_role(current_user)
    if role not in ("pedagogical_admin", "pedagogical_lead"):
        raise HTTPException(status_code=403, detail="Pedagogical access required")
    return current_user


# ---------------------------------------------------------------------------
# School-scoped access check
# ---------------------------------------------------------------------------

def check_school_access(current_user, resource_school_id: int):
    """Verify the current user has access to a school-scoped resource.

    - super_admin / pedagogical_admin: unrestricted access to all schools.
    - admin_school / teacher / student / pedagogical_lead: must own the resource's school_id.
    """
    role = get_user_role(current_user)
    if role in ("super_admin", "pedagogical_admin"):
        return
    if current_user.school_id != resource_school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: resource belongs to another school",
        )


# ---------------------------------------------------------------------------
# Course ownership check
# ---------------------------------------------------------------------------

def check_course_ownership(course, current_user, require_write: bool = False, db=None):
    """Verify the current user has access to a course based on its owner_type.

    - owner_type="school": user must belong to the course's school (via school_id),
      OR be super_admin / pedagogical_admin.
    - owner_type="independent_teacher": only owner_id == current_user.id can modify;
      students enrolled can access content.
    - owner_type="eduai_catalog": accessible if the school has a SchoolCourseAccess
      entry, OR if user is super_admin / pedagogical_admin.

    When require_write=True, stricter rules apply (only owners can modify).
    """
    role = get_user_role(current_user)

    # Super admins and pedagogical admins have full access
    if role in ("super_admin", "pedagogical_admin"):
        return

    owner_type = getattr(course, "owner_type", "school") or "school"

    if owner_type == "school":
        check_school_access(current_user, course.school_id)
        return

    if owner_type == "independent_teacher":
        if require_write:
            if course.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: only the course owner can modify this course",
                )
        else:
            if course.owner_id != current_user.id:
                if db is None:
                    raise HTTPException(
                        status_code=500,
                        detail="check_course_ownership requires a db session for enrollment check",
                    )
                from app.models import CourseEnrollment
                enrollment = db.query(CourseEnrollment).filter(
                    CourseEnrollment.student_id == current_user.id,
                    CourseEnrollment.course_id == course.id,
                ).first()
                if not enrollment:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: you are not enrolled in this course",
                    )
        return

    if owner_type == "eduai_catalog":
        if db is None:
            raise HTTPException(
                status_code=500,
                detail="check_course_ownership requires a db session for catalog access check",
            )
        from app.models import SchoolCourseAccess
        access = db.query(SchoolCourseAccess).filter(
            SchoolCourseAccess.course_id == course.id,
            SchoolCourseAccess.school_id == current_user.school_id,
            SchoolCourseAccess.is_active == True,
        ).first()
        if not access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: your school does not have access to this course",
            )
        return


# ---------------------------------------------------------------------------
# Demo account isolation
# ---------------------------------------------------------------------------

def require_non_demo_access(current_user: User = Depends(set_tenant_context)) -> User:
    """DEPRECATED: Kept for backward compatibility. Tenant filter (C1) handles isolation."""
    return current_user


# ---------------------------------------------------------------------------
# Subscription expiration check (independent paid teachers)
# ---------------------------------------------------------------------------

def require_active_subscription(current_user: User = Depends(set_tenant_context)) -> User:
    """For independent_paid teachers, block creation actions when subscription expired.

    - Does NOT block read/consult actions (viewing existing courses, students, etc.)
    - Only blocks creation of new courses, assignments, and similar write actions.
    - Other subscription plans (trial, school_affiliated) are never blocked.
    """
    from datetime import datetime, timezone
    if getattr(current_user, "subscription_plan", None) == "independent_paid":
        expires = getattr(current_user, "subscription_expires_at", None)
        if expires and expires < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=402,
                detail="Subscription expired. Please renew to continue creating content.",
            )
    return current_user


# ---------------------------------------------------------------------------
# Permission dependencies — Parent role
# ---------------------------------------------------------------------------

def require_parent(current_user: User = Depends(set_tenant_context)) -> User:
    """Require PARENT role. Also sets tenant context."""
    if get_user_role(current_user) != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")
    return current_user
