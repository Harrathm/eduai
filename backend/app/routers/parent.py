"""Parent router — RBAC-guarded endpoints for parent role.

Endpoints:
- GET /parents/me/enfants: list children of the authenticated parent
- GET /parents/me/enfants/{eleve_id}/suivi: read-only view of student progress
- GET /parents/me/dashboard: aggregated dashboard for all children
- POST /parents/me/enfants/lier: link a child by email
- DELETE /parents/me/enfants/{eleve_id}/delier: unlink a child
- GET /parents/me/enfants/{eleve_id}/progression: detailed progress with scores and goals
- POST /parents/me/messages: send a message to a teacher or admin
- GET /parents/me/messages: list messages for the parent
- PUT /parents/me/messages/{message_id}/read: mark a message as read
"""
from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.deps import require_parent
from app.models import (
    User, ParentEnfant, PackPurchase, PackPurchaseStatus,
    ProfilAssimilationEleve, HistoriqueScoreEleve, LearningGoal, GoalStatus,
    CourseEnrollment, StudentBadge, StudentStreak, StudentRanking,
    Message, MessageType,
)
from app.services.wallet import get_dt_balance
from app.services.goal_tracking import compute_goal_status

router = APIRouter(prefix="/parents", tags=["parents"])


class LierEleveRequest(BaseModel):
    email_eleve: EmailStr


def _check_parent_link(db: Session, parent_id: int, eleve_id: int) -> ParentEnfant:
    """Verify parent is linked to the student, return link or raise 403."""
    link = (
        db.query(ParentEnfant)
        .filter(
            ParentEnfant.parent_user_id == parent_id,
            ParentEnfant.eleve_id == eleve_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé: cet élève n'est pas rattaché à votre compte parent.",
        )
    return link


# ---------------------------------------------------------------------------
# List children
# ---------------------------------------------------------------------------

@router.get("/me/enfants")
def list_mes_enfants(
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """List all children linked to the authenticated parent."""
    links = (
        db.query(ParentEnfant)
        .filter(ParentEnfant.parent_user_id == current_user.id)
        .all()
    )
    enfants = []
    now = datetime.now(timezone.utc)
    for link in links:
        eleve = db.query(User).filter(User.id == link.eleve_id).first()
        if eleve is None:
            continue

        active_packs = (
            db.query(PackPurchase)
            .filter(
                PackPurchase.student_id == eleve.id,
                PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
                PackPurchase.valid_until > now,
            )
            .count()
        )

        dt_balance = get_dt_balance(db, eleve.id)

        enfants.append({
            "eleve_id": eleve.id,
            "full_name": eleve.full_name,
            "email": eleve.email,
            "niveau_scolaire": eleve.niveau_scolaire,
            "school_id": eleve.school_id,
            "date_liaison": link.date_creation.isoformat(),
            "dt_balance": dt_balance,
            "packs_actifs_count": active_packs,
        })
    return {"enfants": enfants}


# ---------------------------------------------------------------------------
# Dashboard aggregé multi-enfants
# ---------------------------------------------------------------------------

@router.get("/me/dashboard")
def parent_dashboard(
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """Aggregated dashboard for all children of the parent."""
    links = (
        db.query(ParentEnfant)
        .filter(ParentEnfant.parent_user_id == current_user.id)
        .all()
    )
    if not links:
        return {"enfants": [], "total_dt_depense": 0.0}

    now = datetime.now(timezone.utc)
    total_dt_depense = 0.0
    enfants = []

    for link in links:
        eleve = db.query(User).filter(User.id == link.eleve_id).first()
        if not eleve:
            continue

        dt_balance = get_dt_balance(db, eleve.id)

        active_packs = (
            db.query(PackPurchase)
            .filter(
                PackPurchase.student_id == eleve.id,
                PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
                PackPurchase.valid_until > now,
            )
            .all()
        )
        total_dt_depense += sum(p.amount_paid for p in active_packs)

        badges_count = db.query(StudentBadge).filter(StudentBadge.eleve_id == eleve.id).count()

        streak = (
            db.query(StudentStreak)
            .filter(StudentStreak.eleve_id == eleve.id)
            .order_by(StudentStreak.date_jour.desc())
            .first()
        )
        current_streak = 0
        if streak:
            check_date = streak.date_jour
            while True:
                s = db.query(StudentStreak).filter(
                    StudentStreak.eleve_id == eleve.id,
                    StudentStreak.date_jour == check_date,
                    StudentStreak.streak_login == True,
                ).first()
                if not s:
                    break
                current_streak += 1
                check_date = date.fromordinal(check_date.toordinal() - 1)

        scores = (
            db.query(func.avg(HistoriqueScoreEleve.score))
            .filter(HistoriqueScoreEleve.eleve_id == eleve.id)
            .scalar()
        )

        enfants.append({
            "eleve_id": eleve.id,
            "full_name": eleve.full_name,
            "niveau_scolaire": eleve.niveau_scolaire,
            "dt_balance": dt_balance,
            "packs_actifs_count": len(active_packs),
            "badges_count": badges_count,
            "streak_jours": current_streak,
            "score_moyen": round(float(scores), 1) if scores else None,
        })

    return {
        "enfants": enfants,
        "total_dt_depense": round(total_dt_depense, 2),
    }


# ---------------------------------------------------------------------------
# Suivi détaillé d'un enfant
# ---------------------------------------------------------------------------

@router.get("/me/enfants/{eleve_id}/suivi")
def suivi_eleve(
    eleve_id: int,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """Read-only view of a child's progress (assimilation level, active packs)."""
    _check_parent_link(db, current_user.id, eleve_id)

    eleve = db.query(User).filter(User.id == eleve_id).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable")

    now = datetime.now(timezone.utc)
    active_packs = (
        db.query(PackPurchase)
        .filter(
            PackPurchase.student_id == eleve_id,
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
        )
        .all()
    )
    packs_info = [
        {
            "pack_id": p.pack_id,
            "valid_from": p.valid_from.isoformat() if p.valid_from else None,
            "valid_until": p.valid_until.isoformat() if p.valid_until else None,
            "amount_paid": p.amount_paid,
            "currency": p.currency,
        }
        for p in active_packs
    ]

    dt_balance = get_dt_balance(db, eleve_id)

    return {
        "eleve_id": eleve.id,
        "full_name": eleve.full_name,
        "niveau_scolaire": eleve.niveau_scolaire,
        "dt_balance": dt_balance,
        "packs_actifs": packs_info,
    }


# ---------------------------------------------------------------------------
# Progression détaillée (scores, badges, objectifs)
# ---------------------------------------------------------------------------

@router.get("/me/enfants/{eleve_id}/progression")
def progression_eleve(
    eleve_id: int,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """Detailed progress: scores by chapter, badges, streaks, goals."""
    _check_parent_link(db, current_user.id, eleve_id)

    eleve = db.query(User).filter(User.id == eleve_id).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable")

    # Scores by chapter
    scores = (
        db.query(HistoriqueScoreEleve)
        .filter(HistoriqueScoreEleve.eleve_id == eleve_id)
        .order_by(HistoriqueScoreEleve.date.desc())
        .limit(50)
        .all()
    )
    scores_data = [
        {
            "chapitre_id": s.chapitre_id,
            "score": s.score,
            "date": s.date.isoformat(),
        }
        for s in scores
    ]

    # Badges
    badges = (
        db.query(StudentBadge)
        .filter(StudentBadge.eleve_id == eleve_id)
        .all()
    )
    from app.models import BadgeDefinition
    badges_data = []
    for b in badges:
        badge_def = db.query(BadgeDefinition).filter(BadgeDefinition.id == b.badge_id).first()
        if badge_def:
            badges_data.append({
                "badge_id": badge_def.id,
                "nom": badge_def.nom,
                "description": badge_def.description,
                "icon_url": badge_def.icon_url,
                "couleur": badge_def.couleur,
                "date_obtention": b.date_obtention.isoformat(),
            })

    # Streaks (last 30 days)
    thirty_days_ago = date.fromordinal(date.today().toordinal() - 30)
    streaks = (
        db.query(StudentStreak)
        .filter(
            StudentStreak.eleve_id == eleve_id,
            StudentStreak.date_jour >= thirty_days_ago,
        )
        .order_by(StudentStreak.date_jour.desc())
        .all()
    )
    streaks_data = [
        {
            "date": s.date_jour.isoformat(),
            "streak_login": s.streak_login,
            "streak_quiz": s.streak_quiz,
            "streak_objectif": s.streak_objectif,
            "points_jour": s.points_jour,
        }
        for s in streaks
    ]

    # Active learning goals
    now = datetime.now(timezone.utc)
    goals = (
        db.query(LearningGoal)
        .filter(
            LearningGoal.user_id == eleve_id,
            LearningGoal.period_end >= now,
        )
        .all()
    )
    goals_data = []
    for g in goals:
        status = compute_goal_status(db, g)
        goals_data.append({
            "id": g.id,
            "matiere": g.matiere,
            "horizon": g.horizon,
            "metric_type": g.metric_type,
            "target_value": float(g.target_value),
            "status": status["status"],
            "progress_pct": status.get("progress_pct", 0),
        })

    return {
        "eleve_id": eleve.id,
        "full_name": eleve.full_name,
        "niveau_scolaire": eleve.niveau_scolaire,
        "scores": scores_data,
        "badges": badges_data,
        "streaks": streaks_data,
        "objectifs": goals_data,
    }


# ---------------------------------------------------------------------------
# Lier un enfant (par email)
# ---------------------------------------------------------------------------

@router.post("/me/enfants/lier")
def lier_eleve(
    body: LierEleveRequest,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """Link a child to the parent account by email.

    The child must exist, have role=student, and belong to the same school.
    """
    eleve = (
        db.query(User)
        .filter(User.email == body.email_eleve, User.role == "student")
        .first()
    )
    if not eleve:
        raise HTTPException(status_code=404, detail="Aucun élève trouvé avec cet email.")

    # School isolation: parent and student must belong to the same school
    if current_user.school_id and eleve.school_id and current_user.school_id != eleve.school_id:
        raise HTTPException(
            status_code=403,
            detail="Cet élève n'appartient pas à votre école. Liaison refusée.",
        )

    existing = (
        db.query(ParentEnfant)
        .filter(
            ParentEnfant.parent_user_id == current_user.id,
            ParentEnfant.eleve_id == eleve.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Cet élève est déjà rattaché à votre compte.")

    link = ParentEnfant(
        parent_user_id=current_user.id,
        eleve_id=eleve.id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return {
        "message": "Élève rattaché avec succès.",
        "eleve_id": eleve.id,
        "full_name": eleve.full_name,
    }


# ---------------------------------------------------------------------------
# Délier un enfant
# ---------------------------------------------------------------------------

@router.delete("/me/enfants/{eleve_id}/delier")
def delier_eleve(
    eleve_id: int,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """Unlink a child from the parent account."""
    link = (
        db.query(ParentEnfant)
        .filter(
            ParentEnfant.parent_user_id == current_user.id,
            ParentEnfant.eleve_id == eleve_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Aucune liaison trouvée avec cet élève.")

    db.delete(link)
    db.commit()

    return {"message": "Liaison supprimee avec succes.", "eleve_id": eleve_id}


# ---------------------------------------------------------------------------
# Messagerie parent
# ---------------------------------------------------------------------------

class SendMessageRequest(BaseModel):
    recipient_type: str  # "teacher" or "admin"
    subject: str
    body: str


@router.post("/me/messages")
def send_message(
    body: SendMessageRequest,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """Parent sends a message to a teacher or admin of their children's school."""
    if body.recipient_type not in ("teacher", "admin"):
        raise HTTPException(status_code=400, detail="recipient_type must be 'teacher' or 'admin'")
    if not body.subject.strip() or not body.body.strip():
        raise HTTPException(status_code=400, detail="Subject and body are required")

    # Find a child to determine the school
    link = db.query(ParentEnfant).filter(ParentEnfant.parent_user_id == current_user.id).first()
    if not link:
        raise HTTPException(status_code=400, detail="Aucun enfant rattache. Liez d'abord un eleve.")

    child = db.query(User).filter(User.id == link.eleve_id).first()
    if not child or not child.school_id:
        raise HTTPException(status_code=400, detail="Impossible de determiner l'ecole de l'enfant")

    school_id = child.school_id

    # Find a recipient
    target_role = "teacher" if body.recipient_type == "teacher" else "admin_school"
    recipient = (
        db.query(User)
        .filter(User.school_id == school_id, User.role == target_role, User.is_active == True)
        .first()
    )
    if not recipient:
        # Fallback: try super_admin
        recipient = (
            db.query(User)
            .filter(User.role == "super_admin", User.is_active == True)
            .first()
        )
    if not recipient:
        raise HTTPException(status_code=404, detail="Aucun destinataire disponible")

    msg = Message(
        school_id=school_id,
        sender_id=current_user.id,
        receiver_id=recipient.id,
        type=MessageType.DIRECT,
        subject=body.subject.strip(),
        body=body.body.strip(),
        target_audience=target_role,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {"id": msg.id, "message": "Message envoye avec succes."}


@router.get("/me/messages")
def list_messages(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """List messages visible to the parent (direct + broadcasts)."""
    from sqlalchemy import union_all, select

    direct_q = db.query(Message).filter(
        Message.receiver_id == current_user.id,
        Message.school_id == current_user.school_id,
    )
    broadcast_q = db.query(Message).filter(
        Message.receiver_id.is_(None),
        Message.target_audience.in_(["all", "parents"]),
        Message.school_id == current_user.school_id,
    )

    direct_stmt = direct_q.with_entities(Message.id)
    broadcast_stmt = broadcast_q.with_entities(Message.id)
    combined = direct_stmt.union(broadcast_stmt).subquery()

    query = db.query(Message).filter(Message.id.in_(select(combined.c.id)))
    if unread_only:
        query = query.filter(Message.is_read == False)

    messages = query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": query.count(),
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": m.sender.full_name if m.sender else "Systeme",
                "subject": m.subject,
                "body": m.body,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "is_read": m.is_read,
            }
            for m in messages
        ],
    }


@router.put("/me/messages/{message_id}/read")
def mark_message_read(
    message_id: int,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """Mark a message as read."""
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message introuvable")

    is_direct = msg.receiver_id == current_user.id
    is_broadcast = msg.receiver_id is None and msg.target_audience in ("all", "parents")
    if not is_direct and not is_broadcast:
        raise HTTPException(status_code=403, detail="Acces interdit")

    if not msg.is_read:
        msg.is_read = True
        msg.read_at = datetime.now(timezone.utc)
        db.commit()

    return {"ok": True}
