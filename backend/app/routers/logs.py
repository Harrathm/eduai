"""Backend error log viewer for admin."""

import os
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User, AuditLog
from app.routers.admin import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/logs", tags=["Admin Logs"])


LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "backend.log")


@router.get("/errors")
def get_error_logs(
    lines: int = Query(100, ge=10, le=5000),
    search: Optional[str] = None,
    level: Optional[str] = None,
    admin=Depends(require_admin),
):
    """Read recent backend error logs."""
    if not os.path.exists(LOG_FILE):
        return {"total_lines": 0, "lines": [], "file": LOG_FILE}

    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
    except Exception as e:
        return {"total_lines": 0, "lines": [], "error": str(e)}

    filtered = []
    for line in all_lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if level and level.upper() not in line.upper():
            continue
        if search and search.lower() not in line.lower():
            continue
        filtered.append(line)

    tail = filtered[-lines:] if lines < len(filtered) else filtered

    return {
        "total_lines": len(filtered),
        "lines": tail,
        "file": LOG_FILE,
        "truncated": len(filtered) > lines,
    }


@router.get("/audit")
def get_audit_logs(
    action: Optional[str] = None,
    admin_id: Optional[int] = None,
    target_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """List audit logs with filtering and pagination. Non-super admins see only their school's logs."""
    query = db.query(AuditLog)
    # School isolation: non-super admins only see their school's audit logs
    from app.deps import get_user_role
    if get_user_role(admin) != "super_admin":
        query = query.filter(AuditLog.admin_id == admin.id)
    if action:
        query = query.filter(AuditLog.action == action)
    if admin_id:
        query = query.filter(AuditLog.admin_id == admin_id)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)

    total = query.count()
    logs = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": log.id,
                "admin_id": log.admin_id,
                "admin_email": log.admin_email,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }
