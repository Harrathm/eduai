"""Inbox endpoints for students and teachers to read messages."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.models import Message, User

router = APIRouter(prefix="/inbox", tags=["inbox"])


def _inbox_filter(current_user: User):
    """Build OR filter: direct messages + broadcasts matching role."""
    role = current_user.role
    base_filters = []
    if role not in ("super_admin", "pedagogical_admin"):
        base_filters.append(Message.school_id == current_user.school_id)

    direct = and_(Message.receiver_id == current_user.id, *base_filters)
    broadcast = and_(
        Message.receiver_id.is_(None),
        Message.target_audience.in_(["all", f"{role}s", role]),
        *base_filters,
    )
    return or_(direct, broadcast)


@router.get("/messages")
def list_inbox_messages(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return messages visible to the current user."""
    query = db.query(Message).filter(_inbox_filter(current_user))

    if unread_only:
        query = query.filter(Message.is_read == False)

    total = query.count()
    messages = query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "type": msg.type.value if hasattr(msg.type, "value") else msg.type,
            "subject": msg.subject,
            "body": msg.body,
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.full_name if msg.sender else "Admin",
            "is_read": msg.is_read,
            "created_at": msg.created_at,
            "target_audience": msg.target_audience,
        })

    return {"total": total, "unread": db.query(Message).filter(
        _inbox_filter(current_user), Message.is_read == False,
    ).count(), "items": result}


@router.put("/messages/{message_id}/read")
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a message as read."""
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Verify the user is allowed to read this message
    is_direct = msg.receiver_id == current_user.id
    is_broadcast = msg.receiver_id is None and msg.target_audience in (
        "all", f"{current_user.role}s", current_user.role
    )
    if not is_direct and not is_broadcast:
        raise HTTPException(status_code=403, detail="Access denied")

    if not msg.is_read:
        msg.is_read = True
        msg.read_at = datetime.now(timezone.utc)
        db.commit()

    return {"ok": True}


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the count of unread messages for the current user."""
    count = db.query(Message).filter(
        _inbox_filter(current_user), Message.is_read == False,
    ).count()
    return {"unread_count": count}
