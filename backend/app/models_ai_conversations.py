"""
EDUAI Learning - Modèles pour l'historique des conversations IA
Tables: ai_conversations, ai_chat_messages
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Integer, String, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, utcnow


class AIConversation(Base):
    """Conversation entre un utilisateur et l'assistant IA"""
    __tablename__ = "ai_conversations"
    __table_args__ = (
        Index("ix_ai_conv_user_id", "user_id"),
        Index("ix_ai_conv_updated_at", "updated_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), default="Nouvelle conversation")
    subject: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # Relations
    messages: Mapped[List[AIChatMessage]] = relationship(
        "AIChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIChatMessage.created_at",
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="ai_conversations", foreign_keys=[user_id]
    )


class AIChatMessage(Base):
    """Message unique dans une conversation IA"""
    __tablename__ = "ai_chat_messages"
    __table_args__ = (
        Index("ix_ai_msg_conv_id", "conversation_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" ou "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    detected_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # "ar", "fr", "en"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    # Relations
    conversation: Mapped[AIConversation] = relationship(
        "AIConversation", back_populates="messages"
    )
