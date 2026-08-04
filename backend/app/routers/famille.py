"""
Module B — Famille (compte famille + enfants)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.deps import set_tenant_context, require_parent
from app.models import User, CompteFamille, FamilleEnfant, ParentEnfant
from app.schemas import CompteFamilleRead, FamilleEnfantCreate, FamilleEnfantRead

router = APIRouter(tags=["Module B - Famille"])


@router.get("/famille/compte", response_model=CompteFamilleRead)
def get_compte_famille(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    cf = db.query(CompteFamille).filter(CompteFamille.parent_id == current_user.id).first()
    if not cf:
        cf = CompteFamille(parent_id=current_user.id, max_enfants=5, rang_famille=1)
        db.add(cf)
        db.commit()
        db.refresh(cf)
    return cf


@router.get("/famille/enfants")
def list_enfants(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    cf = db.query(CompteFamille).filter(CompteFamille.parent_id == current_user.id).first()
    if not cf:
        return {"total": 0, "items": []}
    items = db.query(FamilleEnfant).filter(
        FamilleEnfant.compte_famille_id == cf.id
    ).all()
    return {"total": len(items), "items": items}


@router.post("/famille/enfants", response_model=FamilleEnfantRead)
def add_enfant(
    body: FamilleEnfantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    cf = db.query(CompteFamille).filter(CompteFamille.parent_id == current_user.id).first()
    if not cf:
        raise HTTPException(status_code=404, detail="Compte famille non trouvé")

    existing_count = db.query(FamilleEnfant).filter(
        FamilleEnfant.compte_famille_id == cf.id
    ).count()
    if existing_count >= cf.max_enfants:
        raise HTTPException(status_code=400, detail=f"Maximum {cf.max_enfants} enfants atteint")

    already = db.query(FamilleEnfant).filter(FamilleEnfant.eleve_id == body.eleve_id).first()
    if already:
        raise HTTPException(status_code=409, detail="Cet élève est déjà lié à un compte famille")

    # Verify parent_enfant link exists
    link = db.query(ParentEnfant).filter(
        ParentEnfant.parent_user_id == current_user.id,
        ParentEnfant.eleve_id == body.eleve_id,
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="L'élève n'est pas lié à votre compte parent")

    rang = existing_count + 1
    remise_pct = 0.0
    if rang == 2:
        remise_pct = 20.0
    elif rang >= 3:
        remise_pct = 25.0

    enfant = FamilleEnfant(
        compte_famille_id=cf.id,
        eleve_id=body.eleve_id,
        rang=rang,
        remise_pct=remise_pct,
    )
    db.add(enfant)
    db.commit()
    db.refresh(enfant)
    return enfant


@router.delete("/famille/enfants/{enfant_id}")
def remove_enfant(
    enfant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    cf = db.query(CompteFamille).filter(CompteFamille.parent_id == current_user.id).first()
    if not cf:
        raise HTTPException(status_code=404, detail="Compte famille non trouvé")
    enfant = db.query(FamilleEnfant).filter(
        FamilleEnfant.id == enfant_id,
        FamilleEnfant.compte_famille_id == cf.id,
    ).first()
    if not enfant:
        raise HTTPException(status_code=404, detail="Enfant non trouvé")
    db.delete(enfant)

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

    db.commit()
    return {"ok": True}
