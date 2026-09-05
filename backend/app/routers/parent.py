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
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.deps import require_parent
from app.models import (
    User, ParentEnfant, PackPurchase, PackPurchaseStatus,
    ProfilAssimilationEleve, HistoriqueScoreEleve, LearningGoal, GoalStatus,
    CourseEnrollment, StudentBadge, StudentStreak, StudentRanking,
    Message, MessageType, CompteFamille, FamilleEnfant,
)
from app.services.wallet import get_dt_balance
from app.services.goal_tracking import compute_goal_status

router = APIRouter(prefix="/parents", tags=["parents"])


class LierEleveRequest(BaseModel):
    email_eleve: EmailStr
    # M2 FIX — preuve de possession: le parent doit fournir le code
    # d'invitation de l'élève (GET /auth/my-invitation-code).
    invitation_code: str


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
    """Link a child to the parent account by email + invitation code.

    The child must exist, have role=student, belong to the same school, and
    the supplied invitation_code must match the student's own code (M2 FIX).
    """
    eleve = (
        db.query(User)
        .filter(User.email == body.email_eleve, User.role == "student")
        .first()
    )
    if not eleve:
        raise HTTPException(status_code=404, detail="Aucun élève trouvé avec cet email.")

    # M2 FIX — IDOR: l'email seul ne suffit plus. Sans le code d'invitation
    # de l'élève, la liaison est refusée même si l'élève existe et appartient
    # à la même école.
    if not eleve.invitation_code:
        raise HTTPException(
            status_code=403,
            detail="Cet élève n'a pas de code d'invitation actif. Liaison refusee.",
        )
    supplied = (body.invitation_code or "").strip().upper()
    if supplied != eleve.invitation_code.strip().upper():
        raise HTTPException(
            status_code=403,
            detail="Code d'invitation invalide. Demandez le code a votre enfant.",
        )

    # School isolation: parent and student must belong to the same school
    # Reject if either school_id is None (cannot verify) or they differ
    if current_user.school_id is None or eleve.school_id is None:
        raise HTTPException(
            status_code=403,
            detail="Liaison refusee: cannot verify school affiliation (missing school_id).",
        )
    if current_user.school_id != eleve.school_id:
        raise HTTPException(
            status_code=403,
            detail="Cet eleve n'appartient pas a votre ecole. Liaison refusee.",
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

    # M3 FIX — rang familial & remise: sans entrée FamilleEnfant, le rang
    # familial n'est jamais calculé et l'achat de pack applique 0% de remise.
    # On crée automatiquement le CompteFamille du parent (si absent) puis le
    # FamilleEnfant de l'élève avec rang = nb_enfants + 1.
    famille_info = None
    cf = (
        db.query(CompteFamille)
        .filter(CompteFamille.parent_id == current_user.id)
        .first()
    )
    if not cf:
        cf = CompteFamille(parent_id=current_user.id)
        db.add(cf)
        db.flush()
    # FamilleEnfant.eleve_id est UNIQUE (models.py) : un élève n'appartient
    # qu'à une seule famille. Si un autre parent (compte famille différent)
    # l'a déjà rattaché, on ne crée pas de doublon (sinon IntegrityError).
    existing_fe = (
        db.query(FamilleEnfant).filter(FamilleEnfant.eleve_id == eleve.id).first()
    )
    if not existing_fe:
        enfants_count = (
            db.query(FamilleEnfant)
            .filter(FamilleEnfant.compte_famille_id == cf.id)
            .count()
        )
        if enfants_count < cf.max_enfants:
            rang = enfants_count + 1
            remise_pct = 0.0
            if rang == 2:
                remise_pct = 20.0
            elif rang >= 3:
                remise_pct = 25.0
            fe = FamilleEnfant(
                compte_famille_id=cf.id,
                eleve_id=eleve.id,
                rang=rang,
                remise_pct=remise_pct,
            )
            db.add(fe)
            db.flush()
            famille_info = {"rang": rang, "remise_pct": remise_pct}

    db.commit()
    db.refresh(link)

    result = {
        "message": "Élève rattaché avec succès.",
        "eleve_id": eleve.id,
        "full_name": eleve.full_name,
    }
    if famille_info:
        result["famille"] = famille_info
    return result


# ---------------------------------------------------------------------------
# Délier un enfant
# ---------------------------------------------------------------------------

@router.delete("/me/enfants/{eleve_id}/delier")
def delier_eleve(
    eleve_id: int,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """Unlink a child from the parent account.
    Also cascade-deletes the corresponding FamilleEnfant entry to prevent orphans."""
    link = (
        db.query(ParentEnfant)
        .filter(
            ParentEnfant.parent_user_id == current_user.id,
            ParentEnfant.eleve_id == eleve_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Aucune liaison trouvee avec cet eleve.")

    # Cascade-delete the corresponding FamilleEnfant entry (if any)
    from app.models import CompteFamille, FamilleEnfant
    cf = db.query(CompteFamille).filter(CompteFamille.parent_id == current_user.id).first()
    if cf:
        fe = db.query(FamilleEnfant).filter(
            FamilleEnfant.compte_famille_id == cf.id,
            FamilleEnfant.eleve_id == eleve_id,
        ).first()
        if fe:
            db.delete(fe)
            # Re-rank remaining famille enfants
            remaining = db.query(FamilleEnfant).filter(
                FamilleEnfant.compte_famille_id == cf.id
            ).order_by(FamilleEnfant.rang).all()
            for i, e in enumerate(remaining, 1):
                e.rang = i
                if i == 1:
                    e.remise_pct = 0.0
                elif i == 2:
                    e.remise_pct = 20.0
                else:
                    e.remise_pct = 25.0

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
    # M9 FIX — destinataire explicite optionnel. Sans recipient_id, le message
    # part en broadcast à TOUS les enseignants/admins de l'école (plus de
    # .first() arbitraire sur le premier utilisateur trouvé).
    recipient_id: Optional[int] = None


@router.post("/me/messages")
def send_message(
    body: SendMessageRequest,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """Parent sends a message to a teacher or admin of their children's school.

    M9 FIX — deux modes:
    - recipient_id fourni: envoi direct après vérification (même école + rôle
      enseignant/admin).
    - recipient_id absent: broadcast à TOUS les destinataires actifs du rôle
      cible de l'école (fini le choix aléatoire du premier trouvé).
    """
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

    target_role = "teacher" if body.recipient_type == "teacher" else "admin_school"
    allowed_roles = ("teacher", "admin_school")

    if body.recipient_id is not None:
        # Envoi ciblé: le destinataire doit être un enseignant/admin actif de
        # la même école que l'enfant.
        recipient = (
            db.query(User)
            .filter(
                User.id == body.recipient_id,
                User.is_active == True,
                User.role.in_(allowed_roles),
            )
            .first()
        )
        if not recipient:
            raise HTTPException(
                status_code=404,
                detail="Destinataire introuvable ou non enseignant/admin.",
            )
        if recipient.school_id != school_id:
            raise HTTPException(
                status_code=403,
                detail="Ce destinataire n'appartient pas a l'ecole de votre enfant.",
            )
        recipients = [recipient]
    else:
        # Broadcast à tous les destinataires actifs du rôle cible.
        recipients = (
            db.query(User)
            .filter(
                User.school_id == school_id,
                User.role == target_role,
                User.is_active == True,
            )
            .all()
        )

    if not recipients:
        raise HTTPException(status_code=404, detail="Aucun destinataire disponible")

    first_msg_id = None
    for recipient in recipients:
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
        db.flush()
        if first_msg_id is None:
            first_msg_id = msg.id
    db.commit()

    return {
        "id": first_msg_id,
        "sent": len(recipients),
        "message": "Message envoye avec succes.",
    }


@router.get("/me/messages")
def list_messages(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """List messages visible to the parent (direct + broadcasts)."""
    from sqlalchemy import or_, and_

    base_filters = [Message.school_id == current_user.school_id]
    inbox_filter = or_(
        and_(Message.receiver_id == current_user.id, *base_filters),
        and_(
            Message.receiver_id.is_(None),
            Message.target_audience.in_(["all", "parents"]),
            *base_filters,
        ),
    )

    query = db.query(Message).filter(inbox_filter)
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
