"""
Module B — Abonnements (packs + souscription + upgrade)
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.deps import set_tenant_context, require_admin, require_super_admin
from app.models import (
    User, PackDefinition, Abonnement,
    CompteFamille, FamilleEnfant,
)
from app.schemas import (
    PackDefinitionCreate, PackDefinitionRead, PackDefinitionUpdate,
    AbonnementCreate, AbonnementRead,
)

router = APIRouter(tags=["Module B - Abonnements"])

utcnow = lambda: datetime.now(timezone.utc)


@router.get("/abonnements/packs")
def list_packs(
    tier: Optional[str] = None,
    niveau_scolaire: Optional[str] = None,
    est_actif: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    q = db.query(PackDefinition).filter(PackDefinition.est_actif == est_actif)
    if tier:
        q = q.filter(PackDefinition.tier == tier)
    if niveau_scolaire:
        q = q.filter(PackDefinition.niveau_scolaire == niveau_scolaire)
    total = q.count()
    items = q.order_by(PackDefinition.prix_tnd).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/abonnements/packs/{pack_id}", response_model=PackDefinitionRead)
def get_pack(
    pack_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    pack = db.query(PackDefinition).filter(PackDefinition.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return pack


@router.post("/abonnements/packs", response_model=PackDefinitionRead)
def create_pack(
    pack_in: PackDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    pack = PackDefinition(**pack_in.model_dump())
    db.add(pack)
    db.commit()
    db.refresh(pack)
    return pack


@router.put("/abonnements/packs/{pack_id}", response_model=PackDefinitionRead)
def update_pack(
    pack_id: int,
    pack_update: PackDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    pack = db.query(PackDefinition).filter(PackDefinition.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    for field, value in pack_update.model_dump(exclude_unset=True).items():
        setattr(pack, field, value)
    db.commit()
    db.refresh(pack)
    return pack


# ============================================================
# ABONNEMENTS
# ============================================================

@router.post("/abonnements", response_model=AbonnementRead)
def subscribe(
    body: AbonnementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    pack = db.query(PackDefinition).filter(PackDefinition.id == body.pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    existing = db.query(Abonnement).filter(
        Abonnement.user_id == current_user.id,
        Abonnement.statut.in_(["actif", "grace"]),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already have an active subscription")

    now = utcnow()
    duration_days = 90 if pack.tier != "gratuit" else 365
    abonnement = Abonnement(
        user_id=current_user.id,
        pack_id=pack.id,
        statut="actif",
        debut=now,
        fin=now + timedelta(days=duration_days),
    )
    db.add(abonnement)
    db.commit()
    db.refresh(abonnement)
    return abonnement


@router.get("/abonnements/mes-abonnements")
def my_abonnements(
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    items = db.query(Abonnement).filter(
        Abonnement.user_id == current_user.id
    ).order_by(Abonnement.created_at.desc()).all()

    result = []
    for ab in items:
        d = {
            "id": ab.id,
            "user_id": ab.user_id,
            "pack_id": ab.pack_id,
            "statut": ab.statut,
            "debut": ab.debut.isoformat() if ab.debut else None,
            "fin": ab.fin.isoformat() if ab.fin else None,
            "grace_fin": ab.grace_fin.isoformat() if ab.grace_fin else None,
            "created_at": ab.created_at.isoformat() if ab.created_at else None,
            "updated_at": ab.updated_at.isoformat() if ab.updated_at else None,
            "pack": None,
        }
        if ab.pack:
            d["pack"] = {
                "id": ab.pack.id,
                "nom": ab.pack.nom,
                "tier": ab.pack.tier,
                "prix_tnd": ab.pack.prix_tnd,
                "niveau_scolaire": ab.pack.niveau_scolaire,
                "features": ab.pack.features,
            }
        result.append(d)

    return {"total": len(result), "items": result}


@router.put("/abonnements/{abonnement_id}/upgrade", response_model=AbonnementRead)
def upgrade_abonnement(
    abonnement_id: int,
    body: AbonnementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    ab = db.query(Abonnement).filter(
        Abonnement.id == abonnement_id,
        Abonnement.user_id == current_user.id,
    ).first()
    if not ab:
        raise HTTPException(status_code=404, detail="Abonnement not found")

    new_pack = db.query(PackDefinition).filter(PackDefinition.id == body.pack_id).first()
    if not new_pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    TIER_ORDER = {"gratuit": 0, "basique": 1, "silver": 2, "golden": 3}
    if TIER_ORDER.get(new_pack.tier, 0) <= TIER_ORDER.get(ab.pack.tier, 0):
        raise HTTPException(status_code=400, detail="Can only upgrade to a higher tier")

    ab.pack_id = new_pack.id
    ab.updated_at = utcnow()
    db.commit()
    db.refresh(ab)
    return ab


@router.put("/abonnements/{abonnement_id}/cancel", response_model=AbonnementRead)
def cancel_abonnement(
    abonnement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    ab = db.query(Abonnement).filter(
        Abonnement.id == abonnement_id,
        Abonnement.user_id == current_user.id,
    ).first()
    if not ab:
        raise HTTPException(status_code=404, detail="Abonnement not found")
    if ab.statut not in ("actif", "grace"):
        raise HTTPException(status_code=400, detail="Abonnement already cancelled/expired")

    now = utcnow()
    if ab.pack and ab.pack.tier != "gratuit":
        ab.statut = "grace"
        ab.grace_fin = now + timedelta(days=7)
    else:
        ab.statut = "annule"
        ab.fin = now
    ab.updated_at = utcnow()
    db.commit()
    db.refresh(ab)
    return ab
