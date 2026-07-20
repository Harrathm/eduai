import logging
from datetime import datetime, timezone
from typing import Optional

# Configure audit logger
audit_logger = logging.getLogger("audit")


def log_admin_action(
    action: str,
    admin_id: int,
    admin_email: str = "",
    school_id: Optional[int] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    details: Optional[dict] = None,
    success: bool = True,
    db=None,
):
    """Log admin actions — writes to logger AND to audit_logs table when db is provided."""
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "action": action,
        "admin_id": admin_id,
        "school_id": school_id,
        "target_type": target_type,
        "target_id": target_id,
        "details": details or {},
        "success": success,
    }

    if success:
        audit_logger.info(f"ADMIN_ACTION: {action}", extra=log_data)
    else:
        audit_logger.warning(f"ADMIN_ACTION_FAILED: {action}", extra=log_data)

    # Persist to DB when a session is available
    if db is not None:
        try:
            from app.models import AuditLog
            entry = AuditLog(
                admin_id=admin_id,
                admin_email=admin_email or "",
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=str(details) if details else None,
            )
            db.add(entry)
            try:
                db.commit()
            except Exception:
                db.rollback()
        except Exception:
            pass


def log_user_action(
    action: str,
    user_id: int,
    school_id: Optional[int] = None,
    details: Optional[dict] = None,
):
    """Log user actions for audit trail"""
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "action": action,
        "user_id": user_id,
        "school_id": school_id,
        "details": details or {},
    }

    audit_logger.info(f"USER_ACTION: {action}", extra=log_data)


def log_security_event(
    event_type: str,
    details: dict,
    severity: str = "INFO",
):
    """Log security-related events"""
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "event_type": event_type,
        "details": details,
        "severity": severity,
    }

    audit_logger.warning(f"SECURITY: {event_type}", extra=log_data)
