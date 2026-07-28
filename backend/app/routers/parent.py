"""Parent router — RBAC-guarded endpoints for parent role.

Endpoints:
- GET /parents/me/enfants: list children of the authenticated parent
- GET /parents/me/enfants/{eleve_id}/suivi: read-only view of student progress
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_parent
from app.models import User, ParentEnfant, PackPurchase, PackPurchaseStatus
from app.services.wallet import get_dt_balance

router = APIRouter(prefix="/parents", tags=["parents"])


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
    for link in links:
        eleve = db.query(User).filter(User.id == link.eleve_id).first()
        if eleve is None:
            continue
        enfants.append({
            "eleve_id": eleve.id,
            "full_name": eleve.full_name,
            "email": eleve.email,
            "niveau_scolaire": eleve.niveau_scolaire,
            "school_id": eleve.school_id,
            "date_liaison": link.date_creation.isoformat(),
        })
    return {"enfants": enfants}


@router.get("/me/enfants/{eleve_id}/suivi")
def suivi_eleve(
    eleve_id: int,
    current_user: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    """Read-only view of a child's progress (assimilation level, active packs).

    SECURITY: only returns data if the eleve is explicitly linked to the parent
    via ParentEnfant. Never allows access to arbitrary students.
    """
    link = (
        db.query(ParentEnfant)
        .filter(
            ParentEnfant.parent_user_id == current_user.id,
            ParentEnfant.eleve_id == eleve_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(
            status_code=403,
            detail="Accès refusé: cet élève n'est pas rattaché à votre compte parent.",
        )

    eleve = db.query(User).filter(User.id == eleve_id).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable")

    # Active packs
    from datetime import datetime, timezone
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

    # DT balance (derived from ledger)
    dt_balance = get_dt_balance(db, eleve_id)

    return {
        "eleve_id": eleve.id,
        "full_name": eleve.full_name,
        "niveau_scolaire": eleve.niveau_scolaire,
        "dt_balance": dt_balance,
        "packs_actifs": packs_info,
    }
