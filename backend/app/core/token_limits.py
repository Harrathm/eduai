"""Token limit configuration per role. Stored in PlatformSettings as JSON."""

from typing import Optional
from sqlalchemy.orm import Session

from app.services.settings_service import settings_cache

DEFAULT_TOKEN_LIMITS = {
    "student_free": {"monthly": 1000, "daily": 100, "per_request": 50},
    "student_premium": {"monthly": 10000, "daily": 500, "per_request": 200},
    "teacher": {"monthly": 50000, "daily": 2000, "per_request": 500},
    "admin_school": {"monthly": 100000, "daily": 5000, "per_request": 1000},
    "pedagogical_admin": {"monthly": 100000, "daily": 5000, "per_request": 1000},
    "pedagogical_lead": {"monthly": 50000, "daily": 2000, "per_request": 500},
    "super_admin": {"monthly": 1000000, "daily": 50000, "per_request": 5000},
}

SETTINGS_KEY = "token_limits"


def get_token_limits(school_id: int, db: Session) -> dict:
    cached = settings_cache.get_json(school_id, SETTINGS_KEY, db)
    if cached and isinstance(cached, dict):
        return cached
    return dict(DEFAULT_TOKEN_LIMITS)


def get_limit_for_role(
    school_id: int, role: str, db: Session, limit_type: str = "monthly"
) -> int:
    limits = get_token_limits(school_id, db)
    role_key = _role_to_key(role)
    role_limits = limits.get(role_key, DEFAULT_TOKEN_LIMITS.get(role_key, {}))
    return role_limits.get(limit_type, 1000)


def update_token_limits(school_id: int, limits: dict, db: Session) -> dict:
    import json
    settings_cache.set(school_id, SETTINGS_KEY, json.dumps(limits), db)
    return limits


def _role_to_key(role: str) -> str:
    mapping = {
        "student": "student_free",
        "teacher": "teacher",
        "admin_school": "admin_school",
        "pedagogical_admin": "pedagogical_admin",
        "pedagogical_lead": "pedagogical_lead",
        "super_admin": "super_admin",
    }
    return mapping.get(role, "student_free")
