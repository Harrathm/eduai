from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import secrets

from app.db import get_db
from app.auth import get_current_user
from app.models import (
    User, TeacherClass, StudentEnrollment, LiveSession, LiveAttendance,
    LiveSessionStatus,
)
from app.schemas import (
    LiveSessionCreate, LiveSessionUpdate, LiveSessionRead, LiveAttendanceRead,
)

teacher_live_router = APIRouter()


# ─── Helpers ────────────────────────────────────────────────────────────

def _require_teacher(current_user: User = Depends(get_current_user)):
    raw = current_user.role
    role = str(raw.value).upper() if hasattr(raw, 'value') else str(raw).upper().replace('USERROLE.', '')
    if role not in ("TEACHER", "SUPER_ADMIN", "ADMIN_SCHOOL", "PEDAGOGICAL_ADMIN", "PEDAGOGICAL_LEAD"):
        raise HTTPException(status_code=403, detail="Teacher access required")
    return current_user


def _own_class_or_403(db: Session, class_id: int, teacher_id: int):
    tc = db.query(TeacherClass).filter(
        TeacherClass.id == class_id, TeacherClass.teacher_id == teacher_id
    ).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Class not found or not owned by you")
    return tc


def _own_session_or_403(db: Session, session_id: int, teacher_id: int):
    ls = db.query(LiveSession).filter(
        LiveSession.id == session_id, LiveSession.teacher_id == teacher_id
    ).first()
    if not ls:
        raise HTTPException(status_code=404, detail="Live session not found or not owned by you")
    return ls


def _refresh_session_status(session: LiveSession):
    """Automatically update session status based on scheduled_at and duration."""
    now = datetime.now(timezone.utc)
    scheduled = session.scheduled_at
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    if session.status == LiveSessionStatus.UPCOMING.value:
        if scheduled <= now:
            session.status = LiveSessionStatus.LIVE.value
    elif session.status == LiveSessionStatus.LIVE.value:
        end_time = scheduled + timedelta(minutes=session.duration_minutes)
        if now > end_time:
            session.status = LiveSessionStatus.ENDED.value


def _serialize_ls(ls: LiveSession, db: Session) -> dict:
    """Serialize a LiveSession with computed fields."""
    attendance_count = db.query(func.count(LiveAttendance.id)).filter(
        LiveAttendance.live_session_id == ls.id
    ).scalar() or 0
    students_count = db.query(func.count(StudentEnrollment.id)).filter(
        StudentEnrollment.class_id == ls.class_id, StudentEnrollment.is_active == True
    ).scalar() or 0
    teacher_name = ls.teacher.full_name if ls.teacher else None
    class_name = ls.teacher_class.name if ls.teacher_class else None
    return {
        "id": ls.id,
        "teacher_id": ls.teacher_id,
        "class_id": ls.class_id,
        "school_id": ls.school_id,
        "title": ls.title,
        "description": ls.description,
        "scheduled_at": ls.scheduled_at,
        "duration_minutes": ls.duration_minutes,
        "status": ls.status,
        "meeting_url": ls.meeting_url,
        "created_at": ls.created_at,
        "updated_at": ls.updated_at,
        "teacher_name": teacher_name,
        "class_name": class_name,
        "attendance_count": attendance_count,
        "students_count": students_count,
    }


# ═══════════════════════════════════════════════════════════════════════
# TEACHER-FACING ENDPOINTS  (/api/teacher/live-sessions)
# ═══════════════════════════════════════════════════════════════════════


@teacher_live_router.post("/live-sessions", response_model=LiveSessionRead)
def create_live_session(
    body: LiveSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: create a new live session for a class."""
    try:
        tc = _own_class_or_403(db, body.class_id, current_user.id)

        # Generate meeting URL
        random_slug = secrets.token_hex(6)
        meeting_url = f"https://meet.jit.si/eduai-{tc.id}-{random_slug}"

        ls = LiveSession(
            teacher_id=current_user.id,
            class_id=body.class_id,
            school_id=current_user.school_id,
            title=body.title,
            description=body.description,
            scheduled_at=body.scheduled_at,
            duration_minutes=body.duration_minutes,
            status=LiveSessionStatus.UPCOMING.value,
            meeting_url=meeting_url,
        )
        db.add(ls)
        db.commit()
        db.refresh(ls)
        return _serialize_ls(ls, db)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur création séance: {str(e)}")


@teacher_live_router.get("/live-sessions", response_model=List[LiveSessionRead])
def list_my_live_sessions(
    status: Optional[str] = Query(None, description="Filter by status: upcoming, live, ended, cancelled"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: list all my live sessions across all classes."""
    query = db.query(LiveSession).filter(LiveSession.teacher_id == current_user.id)
    if status:
        query = query.filter(LiveSession.status == status)

    sessions = query.order_by(LiveSession.scheduled_at.desc()).offset(skip).limit(limit).all()

    # Auto-refresh statuses
    updated = False
    for ls in sessions:
        old_status = ls.status
        _refresh_session_status(ls)
        if ls.status != old_status:
            updated = True
    if updated:
        db.commit()

    return [_serialize_ls(ls, db) for ls in sessions]


@teacher_live_router.get("/classes/{class_id}/live-sessions", response_model=List[LiveSessionRead])
def list_class_live_sessions(
    class_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: list live sessions for a specific class."""
    _own_class_or_403(db, class_id, current_user.id)

    query = db.query(LiveSession).filter(
        LiveSession.class_id == class_id,
        LiveSession.teacher_id == current_user.id,
    )
    if status:
        query = query.filter(LiveSession.status == status)

    sessions = query.order_by(LiveSession.scheduled_at.desc()).all()

    # Auto-refresh statuses
    updated = False
    for ls in sessions:
        old_status = ls.status
        _refresh_session_status(ls)
        if ls.status != old_status:
            updated = True
    if updated:
        db.commit()

    return [_serialize_ls(ls, db) for ls in sessions]


@teacher_live_router.get("/live-sessions/{session_id}", response_model=LiveSessionRead)
def get_live_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: get details of a live session including attendance list."""
    ls = _own_session_or_403(db, session_id, current_user.id)
    _refresh_session_status(ls)
    db.commit()
    return _serialize_ls(ls, db)


@teacher_live_router.put("/live-sessions/{session_id}", response_model=LiveSessionRead)
def update_live_session(
    session_id: int,
    body: LiveSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: update a live session (only if status is upcoming)."""
    ls = _own_session_or_403(db, session_id, current_user.id)

    if ls.status != LiveSessionStatus.UPCOMING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot modify a session with status '{ls.status}'. Only 'upcoming' sessions can be edited.",
        )

    if body.title is not None:
        ls.title = body.title
    if body.description is not None:
        ls.description = body.description
    if body.scheduled_at is not None:
        ls.scheduled_at = body.scheduled_at
    if body.duration_minutes is not None:
        ls.duration_minutes = body.duration_minutes
    if body.status is not None:
        ls.status = body.status

    ls.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ls)
    return _serialize_ls(ls, db)


@teacher_live_router.delete("/live-sessions/{session_id}")
def cancel_live_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: cancel a live session (soft-cancel, sets status to cancelled)."""
    ls = _own_session_or_403(db, session_id, current_user.id)

    if ls.status in (LiveSessionStatus.ENDED.value, LiveSessionStatus.CANCELLED.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel a session with status '{ls.status}'.",
        )

    ls.status = LiveSessionStatus.CANCELLED.value
    ls.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "cancelled_id": session_id}
