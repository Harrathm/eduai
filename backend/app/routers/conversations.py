"""
Router des conversations IA — CRUD + export PDF/DOCX
Isolation stricte par user_id sur toutes les requêtes.
"""

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import jwt

from app.db import get_db
from app.auth import get_current_user
from app.models import User
from app.models_ai_conversations import AIConversation, AIChatMessage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _get_user_from_query_token(token: str = Query(...), db: Session = Depends(get_db)) -> User:
    """Authentifie un utilisateur via token JWT en query param (pour les exports via window.open)."""
    from app.core.config import get_settings
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable ou désactivé")
    return user


# ── Schémas Pydantic ─────────────────────────────────────

class ConversationSummary(BaseModel):
    id: int
    title: str
    subject: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    message_count: int
    summary: str  # premier extrait des messages

class ConversationDetail(BaseModel):
    id: int
    title: str
    subject: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    messages: list  # [{role, content, created_at, detected_language}]

class MessageCreate(BaseModel):
    role: str  # "user" ou "assistant"
    content: str

class ConversationCreate(BaseModel):
    title: Optional[str] = "Nouvelle conversation"
    subject: Optional[str] = None


# ── Endpoints ────────────────────────────────────────────

@router.get("", response_model=List[ConversationSummary])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Liste les conversations de l'utilisateur connecté (sans les messages)."""
    convs = (
        db.query(AIConversation)
        .filter(AIConversation.user_id == current_user.id)
        .order_by(AIConversation.updated_at.desc())
        .all()
    )
    result = []
    for c in convs:
        count = len(c.messages) if c.messages else 0
        # Résumé : contenu du premier message utilisateur
        summary = ""
        for m in (c.messages or []):
            if m.role == "user":
                summary = m.content[:120] + ("..." if len(m.content) > 120 else "")
                break
        result.append(ConversationSummary(
            id=c.id,
            title=c.title,
            subject=c.subject,
            created_at=c.created_at.isoformat() if c.created_at else None,
            updated_at=c.updated_at.isoformat() if c.updated_at else None,
            message_count=count,
            summary=summary,
        ))
    return result


@router.get("/{conv_id}", response_model=ConversationDetail)
def get_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne le détail complet d'une conversation avec tous ses messages."""
    conv = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conv_id,
            AIConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        subject=conv.subject,
        created_at=conv.created_at.isoformat() if conv.created_at else None,
        updated_at=conv.updated_at.isoformat() if conv.updated_at else None,
        messages=[
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "detected_language": getattr(m, "detected_language", None),
            }
            for m in conv.messages
        ],
    )


@router.post("", response_model=ConversationSummary)
def create_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crée une nouvelle conversation vide."""
    conv = AIConversation(
        user_id=current_user.id,
        title=body.title or "Nouvelle conversation",
        subject=body.subject,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ConversationSummary(
        id=conv.id,
        title=conv.title,
        subject=conv.subject,
        created_at=conv.created_at.isoformat() if conv.created_at else None,
        updated_at=conv.updated_at.isoformat() if conv.updated_at else None,
        message_count=0,
        summary="",
    )


@router.post("/{conv_id}/messages")
def add_message(
    conv_id: int,
    body: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ajoute un message à une conversation (utilisé par le frontend)."""
    conv = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conv_id,
            AIConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    if body.role not in ("user", "assistant"):
        raise HTTPException(status_code=400, detail="Role invalide (user ou assistant).")

    from app.services.export_service import detect_language
    detected = detect_language(body.content)

    msg = AIChatMessage(
        conversation_id=conv.id,
        role=body.role,
        content=body.content,
        detected_language=detected,
    )
    db.add(msg)

    # Mettre à jour updated_at
    from datetime import datetime, timezone
    conv.updated_at = datetime.now(timezone.utc)

    # Si premier message utilisateur, extraire un titre
    if body.role == "user":
        user_msgs = [m for m in conv.messages if m.role == "user"]
        if not user_msgs:
            conv.title = body.content[:80] + ("..." if len(body.content) > 80 else "")

    db.commit()
    return {"ok": True, "message_id": msg.id}


@router.delete("/{conv_id}")
def delete_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Supprime une conversation et tous ses messages (cascade)."""
    conv = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conv_id,
            AIConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    db.delete(conv)
    db.commit()
    return {"ok": True}


@router.delete("")
def delete_all_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Supprime TOUTES les conversations de l'utilisateur connecté."""
    count = (
        db.query(AIConversation)
        .filter(AIConversation.user_id == current_user.id)
        .delete()
    )
    db.commit()
    return {"ok": True, "deleted": count}


# ── Export PDF / DOCX ────────────────────────────────────

@router.get("/{conv_id}/export/pdf")
def export_pdf(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_user_from_query_token),
):
    """Exporte une conversation en PDF avec mise en page EDUAI."""
    conv = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conv_id,
            AIConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")

    from app.services.export_service import export_pdf as make_pdf
    pdf_buf = make_pdf(conv, conv.messages)
    filename = f"conversation_{conv.id}.pdf"
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{conv_id}/export/docx")
def export_docx(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_user_from_query_token),
):
    """Exporte une conversation en DOCX avec mise en page EDUAI."""
    conv = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conv_id,
            AIConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")

    from app.services.export_service import export_docx as make_docx
    docx_buf = make_docx(conv, conv.messages)
    filename = f"conversation_{conv.id}.docx"
    return StreamingResponse(
        docx_buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Export message unique (PDF / DOCX) ────────────────────

class MessageExportRequest(BaseModel):
    content: str
    role: str = "assistant"
    title: Optional[str] = None


@router.post("/export/message/pdf")
def export_message_pdf(
    body: MessageExportRequest,
    current_user: User = Depends(get_current_user),
):
    """Exporte un message unique en PDF avec détection de langue RTL/LTR."""
    from app.services.export_service import export_message_pdf as make_msg_pdf
    pdf_buf = make_msg_pdf(
        message_content=body.content,
        message_role=body.role,
        title=body.title,
    )
    filename = f"message_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/export/message/docx")
def export_message_docx(
    body: MessageExportRequest,
    current_user: User = Depends(get_current_user),
):
    """Exporte un message unique en DOCX avec détection de langue RTL/LTR."""
    from app.services.export_service import export_message_docx as make_msg_docx
    docx_buf = make_msg_docx(
        message_content=body.content,
        message_role=body.role,
        title=body.title,
    )
    filename = f"message_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    return StreamingResponse(
        docx_buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
