"""
Live Sessions - Shared endpoints (join)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.models import (
    User, TeacherClass, StudentEnrollment,
    LiveSession, LiveAttendance, LiveSessionStatus,
)

router = APIRouter()


def _get_user_role(user: User) -> str:
    raw = user.role
    return str(raw.value).upper() if hasattr(raw, "value") else str(raw).upper().replace("USERROLE.", "")


def _is_teacher_or_admin(user: User) -> bool:
    role = _get_user_role(user)
    return role in ("TEACHER", "SUPER_ADMIN", "ADMIN_SCHOOL", "PEDAGOGICAL_ADMIN", "PEDAGOGICAL_LEAD")


def _is_class_member(db: Session, user: User, class_id: int) -> bool:
    """Check if user is the class teacher, an admin, or an enrolled student."""
    role = _get_user_role(user)
    if role in ("SUPER_ADMIN", "PEDAGOGICAL_ADMIN"):
        return True
    if _is_teacher_or_admin(user):
        tc = db.query(TeacherClass).filter(
            TeacherClass.id == class_id, TeacherClass.teacher_id == user.id
        ).first()
        return tc is not None
    enrollment = db.query(StudentEnrollment).filter(
        StudentEnrollment.student_id == user.id,
        StudentEnrollment.class_id == class_id,
        StudentEnrollment.is_active == True,
    ).first()
    return enrollment is not None


@router.post("/live-sessions/{session_id}/join")
def join_live_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Join a live session. Returns the meeting URL stored at creation time."""
    ls = db.query(LiveSession).filter(LiveSession.id == session_id).first()
    if not ls:
        raise HTTPException(status_code=404, detail="Live session not found")

    if not _is_class_member(db, current_user, ls.class_id):
        raise HTTPException(status_code=403, detail="You are not a member of this class")

    # --- ABAC: verify student has course access for at least one course in this class ---
    if not _is_teacher_or_admin(current_user):
        from app.models import ClassCourseAccess, Course
        from app.services.course_access import has_course_access

        class_courses = (
            db.query(ClassCourseAccess.course_id)
            .filter(
                ClassCourseAccess.class_id == ls.class_id,
                ClassCourseAccess.is_active == True,
            )
            .all()
        )
        if class_courses:
            has_access = False
            for (course_id,) in class_courses:
                course = db.query(Course).filter(Course.id == course_id).first()
                if course and has_course_access(current_user, course, db):
                    has_access = True
                    break
            if not has_access:
                raise HTTPException(
                    status_code=403,
                    detail="Pack invalide ou acces non autorise pour les cours de cette classe",
                )

    from app.routers.teacher_live_sessions import _refresh_session_status
    old_status = ls.status
    _refresh_session_status(ls)
    if ls.status != old_status:
        db.commit()

    if ls.status not in (LiveSessionStatus.UPCOMING.value, LiveSessionStatus.LIVE.value):
        raise HTTPException(
            status_code=403,
            detail=f"This session is {ls.status} and cannot be joined",
        )

    if not _is_teacher_or_admin(current_user):
        attendance = db.query(LiveAttendance).filter(
            LiveAttendance.live_session_id == ls.id,
            LiveAttendance.student_id == current_user.id,
        ).first()
        now = datetime.now(timezone.utc)
        if attendance:
            attendance.joined_at = attendance.joined_at or now
            attendance.is_active = True
        else:
            attendance = LiveAttendance(
                live_session_id=ls.id,
                student_id=current_user.id,
                joined_at=now,
                is_active=True,
            )
            db.add(attendance)
        db.commit()

    return {
        "meeting_url": ls.meeting_url,
        "room_name": ls.meeting_url.rsplit("/", 1)[-1] if ls.meeting_url else None,
    }
