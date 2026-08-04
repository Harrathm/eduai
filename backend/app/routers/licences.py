"""
Module B — Licences École (pool + assignation)
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.auth import get_current_user
from app.deps import set_tenant_context, require_school_admin, require_admin
from app.models import (
    User, LicenceEcole, LicenceAssignation, PackDefinition,
)
from app.schemas import (
    LicenceEcoleCreate, LicenceEcoleRead,
    LicenceAssignationCreate, LicenceAssignationRead,
)

router = APIRouter(tags=["Module B - Licences"])

utcnow = lambda: datetime.now(timezone.utc)


@router.get("/ecole/licences")
def list_licences(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    items = db.query(LicenceEcole).filter(
        LicenceEcole.ecole_id == current_user.school_id
    ).all()
    return {"total": len(items), "items": items}


@router.post("/ecole/licences", response_model=LicenceEcoleRead)
def create_licence(
    body: LicenceEcoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    pack = db.query(PackDefinition).filter(PackDefinition.id == body.pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    licence = LicenceEcole(
        ecole_id=current_user.school_id,
        pack_id=body.pack_id,
        quantite=body.quantite,
        quantite_disponible=body.quantite,
    )
    db.add(licence)
    db.commit()
    db.refresh(licence)
    return licence


@router.post("/ecole/licences/{licence_id}/assign", response_model=LicenceAssignationRead)
def assign_licence(
    licence_id: int,
    body: LicenceAssignationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    licence = db.query(LicenceEcole).filter(
        LicenceEcole.id == licence_id,
        LicenceEcole.ecole_id == current_user.school_id,
    ).first()
    if not licence:
        raise HTTPException(status_code=404, detail="Licence not found")
    if licence.quantite_disponible <= 0:
        raise HTTPException(status_code=400, detail="No licences available")

    from app.models import check_school_access
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="User belongs to another school")

    already = db.query(LicenceAssignation).filter(
        LicenceAssignation.licence_id == licence_id,
        LicenceAssignation.user_id == body.user_id,
        LicenceAssignation.desaffecte_a.is_(None),
    ).first()
    if already:
        raise HTTPException(status_code=409, detail="User already has this licence")

    assignation = LicenceAssignation(
        licence_id=licence_id,
        user_id=body.user_id,
        affecte_par_id=current_user.id,
    )
    licence.quantite_disponible -= 1
    db.add(assignation)
    db.commit()
    db.refresh(assignation)
    return assignation


@router.delete("/ecole/licences/{licence_id}/unassign/{user_id}")
def unassign_licence(
    licence_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    licence = db.query(LicenceEcole).filter(
        LicenceEcole.id == licence_id,
        LicenceEcole.ecole_id == current_user.school_id,
    ).first()
    if not licence:
        raise HTTPException(status_code=404, detail="Licence not found")

    assignation = db.query(LicenceAssignation).filter(
        LicenceAssignation.licence_id == licence_id,
        LicenceAssignation.user_id == user_id,
        LicenceAssignation.desaffecte_a.is_(None),
    ).first()
    if not assignation:
        raise HTTPException(status_code=404, detail="Active assignment not found")

    assignation.desaffecte_a = utcnow()
    licence.quantite_disponible += 1
    db.commit()
    return {"ok": True}


@router.get("/ecole/licences/stats")
def licence_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    licences = db.query(LicenceEcole).filter(
        LicenceEcole.ecole_id == current_user.school_id
    ).all()

    total = sum(l.quantite for l in licences)
    disponible = sum(l.quantite_disponible for l in licences)
    utilise = total - disponible

    by_pack = []
    for l in licences:
        pack = db.query(PackDefinition).filter(PackDefinition.id == l.pack_id).first()
        by_pack.append({
            "licence_id": l.id,
            "pack_nom": pack.nom if pack else "?",
            "pack_tier": pack.tier if pack else "?",
            "quantite": l.quantite,
            "disponible": l.quantite_disponible,
            "utilise": l.quantite - l.quantite_disponible,
        })

    return {
        "total": total,
        "disponible": disponible,
        "utilise": utilise,
        "by_pack": by_pack,
    }
