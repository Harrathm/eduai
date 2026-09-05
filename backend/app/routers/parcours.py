"""
Module A — Parcours / Chapitres / Leçons / Paragraphes CRUD
"""
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.deps import (
    set_tenant_context,
    check_school_access,
    require_teacher_or_admin,
    require_admin,
    require_super_admin,
    get_user_role,
)
from app.models import (
    User, Parcours, Chapitre, Lecon, Paragraphe,
)
from app.schemas import (
    ParcoursCreate, ParcoursRead, ParcoursUpdate,
    ChapitreCreate, ChapitreRead, ChapitreUpdate,
    LeconCreate, LeconRead, LeconUpdate,
    ParagrapheCreate, ParagrapheRead, ParagrapheUpdate,
)

router = APIRouter(tags=["Module A - Parcours"])

utcnow = lambda: datetime.now(timezone.utc)

_ADMIN_ROLES = {"super_admin", "admin_school", "pedagogical_admin", "pedagogical_lead"}


def _check_write_access(owner_id: Optional[int], user: User):
    """Allow author OR admin roles to write."""
    if owner_id and owner_id == user.id:
        return
    if get_user_role(user) in _ADMIN_ROLES:
        return
    raise HTTPException(status_code=403, detail="Only the author or an admin can modify this resource")


def _parcours_id_from_chapitre(db: Session, chapitre_id: int) -> Optional[int]:
    row = db.query(Chapitre.parcours_id).filter(Chapitre.id == chapitre_id).first()
    return row[0] if row else None


def _parcours_id_from_lecon(db: Session, lecon_id: int) -> Optional[int]:
    row = (
        db.query(Chapitre.parcours_id)
        .join(Lecon, Lecon.chapitre_id == Chapitre.id)
        .filter(Lecon.id == lecon_id)
        .first()
    )
    return row[0] if row else None


def _parcours_id_from_paragraphe(db: Session, paragraphe_id: int) -> Optional[int]:
    row = (
        db.query(Chapitre.parcours_id)
        .join(Lecon, Lecon.chapitre_id == Chapitre.id)
        .join(Paragraphe, Paragraphe.lecon_id == Lecon.id)
        .filter(Paragraphe.id == paragraphe_id)
        .first()
    )
    return row[0] if row else None


def _check_parcours_ownership(parcours_id: Optional[int], user: User, db: Session) -> None:
    """Resolve the parent parcours and enforce author-or-admin write access."""
    if parcours_id is None:
        raise HTTPException(status_code=404, detail="Ressource parente introuvable")
    parcours = db.query(Parcours).filter(Parcours.id == parcours_id).first()
    if not parcours:
        raise HTTPException(status_code=404, detail="Parcours not found")
    _check_write_access(parcours.auteur_id, user)


# ============================================================
# PARCOURS
# ============================================================

@router.get("/parcours")
def list_parcours(
    skip: int = 0,
    limit: int = 20,
    matiere: Optional[str] = None,
    niveau_scolaire: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    q = db.query(Parcours).filter(Parcours.est_actif == True)

    if matiere:
        q = q.filter(Parcours.matiere == matiere)
    if niveau_scolaire:
        q = q.filter(Parcours.niveau_scolaire == niveau_scolaire)
    if search:
        q = q.filter(Parcours.titre.ilike(f"%{search}%"))

    total = q.count()
    items = q.order_by(Parcours.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.post("/parcours", response_model=ParcoursRead)
def create_parcours(
    parcours_in: ParcoursCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    parcours = Parcours(
        **parcours_in.model_dump(),
        auteur_id=current_user.id,
    )
    db.add(parcours)
    db.commit()
    db.refresh(parcours)
    return parcours


@router.get("/parcours/{parcours_id}", response_model=ParcoursRead)
def get_parcours(
    parcours_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    parcours = db.query(Parcours).filter(Parcours.id == parcours_id).first()
    if not parcours:
        raise HTTPException(status_code=404, detail="Parcours not found")
    return parcours


@router.put("/parcours/{parcours_id}", response_model=ParcoursRead)
@router.patch("/parcours/{parcours_id}", response_model=ParcoursRead)
def update_parcours(
    parcours_id: int,
    parcours_update: ParcoursUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    parcours = db.query(Parcours).filter(Parcours.id == parcours_id).first()
    if not parcours:
        raise HTTPException(status_code=404, detail="Parcours not found")
    _check_write_access(parcours.auteur_id, current_user)
    for field, value in parcours_update.model_dump(exclude_unset=True).items():
        setattr(parcours, field, value)
    parcours.updated_at = utcnow()
    db.commit()
    db.refresh(parcours)
    return parcours


@router.delete("/parcours/{parcours_id}")
def delete_parcours(
    parcours_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    parcours = db.query(Parcours).filter(Parcours.id == parcours_id).first()
    if not parcours:
        raise HTTPException(status_code=404, detail="Parcours not found")
    _check_write_access(parcours.auteur_id, current_user)
    db.delete(parcours)
    db.commit()
    return {"ok": True}


# ============================================================
# CHAPITRES
# ============================================================

@router.get("/parcours/{parcours_id}/chapitres")
def list_chapitres(
    parcours_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    parcours = db.query(Parcours).filter(Parcours.id == parcours_id).first()
    if not parcours:
        raise HTTPException(status_code=404, detail="Parcours not found")
    items = db.query(Chapitre).filter(
        Chapitre.parcours_id == parcours_id
    ).order_by(Chapitre.ordre).all()
    return {"total": len(items), "items": items}


@router.post("/parcours/{parcours_id}/chapitres", response_model=ChapitreRead)
def create_chapitre(
    parcours_id: int,
    chapitre_in: ChapitreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    parcours = db.query(Parcours).filter(Parcours.id == parcours_id).first()
    if not parcours:
        raise HTTPException(status_code=404, detail="Parcours not found")
    _check_parcours_ownership(parcours.id, current_user, db)
    chapitre = Chapitre(parcours_id=parcours_id, **chapitre_in.model_dump())
    db.add(chapitre)
    db.commit()
    db.refresh(chapitre)
    return chapitre


@router.put("/chapitres/{chapitre_id}", response_model=ChapitreRead)
@router.patch("/chapitres/{chapitre_id}", response_model=ChapitreRead)
def update_chapitre(
    chapitre_id: int,
    chapitre_update: ChapitreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    chapitre = db.query(Chapitre).filter(Chapitre.id == chapitre_id).first()
    if not chapitre:
        raise HTTPException(status_code=404, detail="Chapitre not found")
    _check_parcours_ownership(chapitre.parcours_id, current_user, db)
    for field, value in chapitre_update.model_dump(exclude_unset=True).items():
        setattr(chapitre, field, value)
    chapitre.updated_at = utcnow()
    db.commit()
    db.refresh(chapitre)
    return chapitre


@router.delete("/chapitres/{chapitre_id}")
def delete_chapitre(
    chapitre_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    chapitre = db.query(Chapitre).filter(Chapitre.id == chapitre_id).first()
    if not chapitre:
        raise HTTPException(status_code=404, detail="Chapitre not found")
    _check_parcours_ownership(chapitre.parcours_id, current_user, db)
    db.delete(chapitre)
    db.commit()
    return {"ok": True}


# ============================================================
# LEÇONS
# ============================================================

@router.get("/chapitres/{chapitre_id}/lecons")
def list_lecons(
    chapitre_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    chapitre = db.query(Chapitre).filter(Chapitre.id == chapitre_id).first()
    if not chapitre:
        raise HTTPException(status_code=404, detail="Chapitre not found")
    items = db.query(Lecon).filter(
        Lecon.chapitre_id == chapitre_id
    ).order_by(Lecon.ordre).all()
    return {"total": len(items), "items": items}


@router.post("/chapitres/{chapitre_id}/lecons", response_model=LeconRead)
def create_lecon(
    chapitre_id: int,
    lecon_in: LeconCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    chapitre = db.query(Chapitre).filter(Chapitre.id == chapitre_id).first()
    if not chapitre:
        raise HTTPException(status_code=404, detail="Chapitre not found")
    _check_parcours_ownership(chapitre.parcours_id, current_user, db)
    lecon = Lecon(chapitre_id=chapitre_id, **lecon_in.model_dump())
    db.add(lecon)
    db.commit()
    db.refresh(lecon)
    return lecon


@router.put("/lecons/{lecon_id}", response_model=LeconRead)
@router.patch("/lecons/{lecon_id}", response_model=LeconRead)
def update_lecon(
    lecon_id: int,
    lecon_update: LeconUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    lecon = db.query(Lecon).filter(Lecon.id == lecon_id).first()
    if not lecon:
        raise HTTPException(status_code=404, detail="Lecon not found")
    _check_parcours_ownership(_parcours_id_from_lecon(db, lecon.id), current_user, db)
    for field, value in lecon_update.model_dump(exclude_unset=True).items():
        setattr(lecon, field, value)
    lecon.updated_at = utcnow()
    db.commit()
    db.refresh(lecon)
    return lecon


@router.delete("/lecons/{lecon_id}")
def delete_lecon(
    lecon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    lecon = db.query(Lecon).filter(Lecon.id == lecon_id).first()
    if not lecon:
        raise HTTPException(status_code=404, detail="Lecon not found")
    _check_parcours_ownership(_parcours_id_from_lecon(db, lecon.id), current_user, db)
    db.delete(lecon)
    db.commit()
    return {"ok": True}


# ============================================================
# PROMOTE / DEMOTE
# ============================================================

class DemoteRequest(BaseModel):
    target_chapitre_id: int


@router.post("/lecons/{lecon_id}/promote", response_model=ChapitreRead)
def promote_lecon_to_chapitre(
    lecon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    Promote a leçon to a chapitre in the same parcours.
    The leçon's paragraphes are moved to a new leçon under the new chapitre.
    """
    lecon = db.query(Lecon).filter(Lecon.id == lecon_id).first()
    if not lecon:
        raise HTTPException(status_code=404, detail="Leçon not found")

    source_chapitre = db.query(Chapitre).filter(Chapitre.id == lecon.chapitre_id).first()
    if not source_chapitre:
        raise HTTPException(status_code=404, detail="Chapitre source not found")
    _check_write_access(source_chapitre.parcours.auteur_id if source_chapitre.parcours else None, current_user)

    max_ordre = db.query(Chapitre).filter(
        Chapitre.parcours_id == source_chapitre.parcours_id
    ).count()

    new_chapitre = Chapitre(
        parcours_id=source_chapitre.parcours_id,
        titre=lecon.titre,
        description=lecon.description,
        objectifs=lecon.objectifs,
        ordre=max_ordre,
    )
    db.add(new_chapitre)
    db.flush()

    new_lecon = Lecon(
        chapitre_id=new_chapitre.id,
        titre=lecon.titre,
        description=lecon.description,
        duree_minutes=lecon.duree_minutes,
        objectifs=lecon.objectifs,
        ordre=0,
    )
    db.add(new_lecon)
    db.flush()

    paragraphes = db.query(Paragraphe).filter(Paragraphe.lecon_id == lecon_id).all()
    for p in paragraphes:
        p.lecon_id = new_lecon.id

    db.delete(lecon)
    db.commit()
    db.refresh(new_chapitre)
    return new_chapitre


@router.post("/chapitres/{chapitre_id}/demote", response_model=LeconRead)
def demote_chapitre_to_lecon(
    chapitre_id: int,
    req: DemoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    Demote a chapitre to a leçon under target_chapitre.
    All child leçons of the demoted chapitre are moved to the target chapitre.
    """
    chapitre = db.query(Chapitre).filter(Chapitre.id == chapitre_id).first()
    if not chapitre:
        raise HTTPException(status_code=404, detail="Chapitre not found")
    _check_write_access(chapitre.parcours.auteur_id if chapitre.parcours else None, current_user)

    target = db.query(Chapitre).filter(Chapitre.id == req.target_chapitre_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target chapitre not found")
    if target.parcours_id != chapitre.parcours_id:
        raise HTTPException(status_code=400, detail="Target chapitre must be in the same parcours")
    if target.id == chapitre.id:
        raise HTTPException(status_code=400, detail="Cannot demote a chapitre to itself")

    max_lecon_ordre = db.query(Lecon).filter(
        Lecon.chapitre_id == target.id
    ).count()

    new_lecon = Lecon(
        chapitre_id=target.id,
        titre=chapitre.titre,
        description=chapitre.description,
        objectifs=chapitre.objectifs,
        ordre=max_lecon_ordre,
    )
    db.add(new_lecon)
    db.flush()

    child_lecons = db.query(Lecon).filter(Lecon.chapitre_id == chapitre_id).all()
    for cl in child_lecons:
        cl.chapitre_id = target.id

    db.delete(chapitre)
    db.commit()
    db.refresh(new_lecon)
    return new_lecon


# ============================================================
# PARAGRAPHES
# ============================================================

@router.get("/lecons/{lecon_id}/paragraphes")
def list_paragraphes(
    lecon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    lecon = db.query(Lecon).filter(Lecon.id == lecon_id).first()
    if not lecon:
        raise HTTPException(status_code=404, detail="Lecon not found")
    items = db.query(Paragraphe).filter(
        Paragraphe.lecon_id == lecon_id
    ).order_by(Paragraphe.ordre).all()
    return {"total": len(items), "items": items}


@router.post("/lecons/{lecon_id}/paragraphes", response_model=ParagrapheRead)
def create_paragraphe(
    lecon_id: int,
    paragraphe_in: ParagrapheCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    lecon = db.query(Lecon).filter(Lecon.id == lecon_id).first()
    if not lecon:
        raise HTTPException(status_code=404, detail="Lecon not found")
    _check_parcours_ownership(_parcours_id_from_lecon(db, lecon.id), current_user, db)
    paragraphe = Paragraphe(lecon_id=lecon_id, **paragraphe_in.model_dump())
    db.add(paragraphe)
    db.commit()
    db.refresh(paragraphe)
    return paragraphe


@router.put("/paragraphes/{paragraphe_id}", response_model=ParagrapheRead)
@router.patch("/paragraphes/{paragraphe_id}", response_model=ParagrapheRead)
def update_paragraphe(
    paragraphe_id: int,
    paragraphe_update: ParagrapheUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    paragraphe = db.query(Paragraphe).filter(Paragraphe.id == paragraphe_id).first()
    if not paragraphe:
        raise HTTPException(status_code=404, detail="Paragraphe not found")
    _check_parcours_ownership(_parcours_id_from_paragraphe(db, paragraphe.id), current_user, db)
    for field, value in paragraphe_update.model_dump(exclude_unset=True).items():
        setattr(paragraphe, field, value)
    paragraphe.updated_at = utcnow()
    db.commit()
    db.refresh(paragraphe)
    return paragraphe


@router.delete("/paragraphes/{paragraphe_id}")
def delete_paragraphe(
    paragraphe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    paragraphe = db.query(Paragraphe).filter(Paragraphe.id == paragraphe_id).first()
    if not paragraphe:
        raise HTTPException(status_code=404, detail="Paragraphe not found")
    _check_parcours_ownership(_parcours_id_from_paragraphe(db, paragraphe.id), current_user, db)
    db.delete(paragraphe)
    db.commit()
    return {"ok": True}
