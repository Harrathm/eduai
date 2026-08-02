"""Notification service for broadcast and direct messaging."""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import User, Message, MessageType, UserRole


# ---------------------------------------------------------------------------
# System sender — used when notifications are triggered by the platform
# (badges, goals, enrollments) rather than by a specific admin.
# ---------------------------------------------------------------------------

_SYSTEM_SENDER_CACHE: Optional[int] = None

SYSTEM_SENDER_EMAIL = "system@eduai.tn"


def _get_system_sender_id(db: Session) -> int:
    """Return the ID of the system sender user, creating it if needed.

    The system user is a super_admin with email ``system@eduai.tn``.
    The ID is cached in-process to avoid repeated lookups.
    """
    global _SYSTEM_SENDER_CACHE
    if _SYSTEM_SENDER_CACHE is not None:
        return _SYSTEM_SENDER_CACHE

    user = db.query(User).filter(User.email == SYSTEM_SENDER_EMAIL).first()
    if user:
        _SYSTEM_SENDER_CACHE = user.id
        return user.id

    # Create the system user on first use
    from app.core.security import get_password_hash
    user = User(
        email=SYSTEM_SENDER_EMAIL,
        hashed_password=get_password_hash("SYSTEM_NO_LOGIN"),
        full_name="EDUAI Système",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        is_approved=True,
        school_id=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _SYSTEM_SENDER_CACHE = user.id
    return user.id


class TargetAudience:
    ALL = "all"
    TEACHERS_ONLY = "teachers_only"
    STUDENTS_ONLY = "students_only"
    ADMINS_ONLY = "admins_only"


class NotificationService:
    def __init__(self, db: Session, sender_id: Optional[int] = None, school_id: Optional[int] = None):
        self.db = db
        self.sender_id = sender_id or _get_system_sender_id(db)
        self.school_id = school_id

    def _get_audience_query(self, target: str):
        query = self.db.query(User).filter(User.is_active == True)
        if self.school_id:
            query = query.filter(User.school_id == self.school_id)
        if target == TargetAudience.TEACHERS_ONLY:
            query = query.filter(User.role == UserRole.TEACHER)
        elif target == TargetAudience.STUDENTS_ONLY:
            query = query.filter(User.role == UserRole.STUDENT)
        elif target == TargetAudience.ADMINS_ONLY:
            query = query.filter(
                or_(
                    User.role == UserRole.ADMIN_SCHOOL,
                    User.role == UserRole.SUPER_ADMIN,
                    User.role == UserRole.PEDAGOGICAL_ADMIN,
                    User.role == UserRole.PEDAGOGICAL_LEAD,
                )
            )
        return query

    def get_audience_count(self, target: str) -> int:
        return self._get_audience_query(target).count()

    def broadcast(self, subject: str, body: str, target: str) -> list[Message]:
        users = self._get_audience_query(target).all()
        messages = []
        for user in users:
            msg = Message(
                school_id=user.school_id or self.school_id or 1,
                sender_id=self.sender_id,
                receiver_id=user.id,
                type=MessageType.BROADCAST,
                subject=subject,
                body=body,
                target_audience=target,
                recipient_role=user.role.value if hasattr(user.role, "value") else str(user.role),
            )
            self.db.add(msg)
            messages.append(msg)
        self.db.commit()
        return messages

    def send_direct(self, receiver_id: int, subject: str, body: str) -> Message:
        receiver = self.db.query(User).filter(User.id == receiver_id).first()
        msg = Message(
            school_id=receiver.school_id or self.school_id or 1,
            sender_id=self.sender_id,
            receiver_id=receiver_id,
            type=MessageType.DIRECT,
            subject=subject,
            body=body,
            target_audience="direct",
        )
        self.db.add(msg)
        self.db.commit()
        return msg


def notify_badge_earned(user_id: int, badge_name: str, db: Session):
    """Notifie un élève quand il gagne un badge."""
    svc = NotificationService(db, school_id=None)
    svc.send_direct(
        receiver_id=user_id,
        subject=f"Badge obtenu : {badge_name}",
        body=f"Félicitations ! Tu as obtenu le badge « {badge_name} ». Continue comme ça !",
    )


def notify_goal_status(user_id: int, horizon: str, status: str, progress_pct: float, db: Session):
    """Notifie un élève quand un objectif change de statut."""
    if status == "completed":
        subject = f"Objectif {horizon} atteint !"
        body = f"Bravo ! Ton objectif {horizon} est atteint ({progress_pct:.0f}%)."
    elif status == "missed":
        subject = f"Objectif {horizon} non atteint"
        body = f"Ton objectif {horizon} n'est pas atteint ({progress_pct:.0f}%). Analyse les résultats et repars plus fort."
    else:
        return  # on_track/behind : pas de notification
    svc = NotificationService(db, school_id=None)
    svc.send_direct(user_id, subject, body)


def notify_enrollment(teacher_id: int, student_name: str, course_title: str, school_id: int, db: Session):
    """Notifie un enseignant qu'un élève s'est inscrit à son cours."""
    svc = NotificationService(db, school_id=school_id)
    svc.send_direct(
        receiver_id=teacher_id,
        subject="Nouvel inscription",
        body=f"{student_name} s'est inscrit à ton cours « {course_title} ».",
    )


def notify_purchase(teacher_id: int, student_name: str, course_title: str, amount: float, school_id: int, db: Session):
    """Notifie un enseignant d'une vente de cours."""
    svc = NotificationService(db, school_id=school_id)
    svc.send_direct(
        receiver_id=teacher_id,
        subject="Nouvelle vente",
        body=f"{student_name} a acheté ton cours « {course_title} » pour {amount:.2f} TND.",
    )
