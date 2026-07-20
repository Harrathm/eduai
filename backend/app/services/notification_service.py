"""Notification service for broadcast messaging."""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import User, Message, MessageType, UserRole


class TargetAudience:
    ALL = "all"
    TEACHERS_ONLY = "teachers_only"
    STUDENTS_ONLY = "students_only"
    ADMINS_ONLY = "admins_only"


class NotificationService:
    def __init__(self, db: Session, sender_id: int, school_id: Optional[int] = None):
        self.db = db
        self.sender_id = sender_id
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
