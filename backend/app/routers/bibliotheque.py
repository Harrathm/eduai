"""
Module A — Bibliothèque globale (recherche + compétences)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.deps import set_tenant_context, require_pedagogical_any, require_admin
from app.models import User, ElementPedagogique, Competence
from app.schemas import CompetenceCreate, CompetenceRead

router = APIRouter(tags=["Module A - Bibliothèque"])


@router.get("/bibliotheque/search")
def search_elements(
    q: Optional[str] = None,
    type: Optional[str] = None,
    matiere: Optional[str] = None,
    niveau_scolaire: Optional[str] = None,
    difficulte: Optional[str] = None,
    est_global: bool = True,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    query = db.query(ElementPedagogique).filter(
        ElementPedagogique.statut == "publie",
        ElementPedagogique.est_global == est_global,
    )
    if q:
        query = query.filter(ElementPedagogique.titre.ilike(f"%{q}%"))
    if type:
        query = query.filter(ElementPedagogique.type == type)
    if matiere:
        query = query.filter(ElementPedagogique.matiere_id.isnot(None))
    if niveau_scolaire:
        query = query.filter(ElementPedagogique.niveau_etude_id.isnot(None))
    if difficulte:
        query = query.filter(ElementPedagogique.difficulte == difficulte)

    total = query.count()
    items = query.order_by(ElementPedagogique.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/bibliotheque/competences")
def list_competences(
    matiere: Optional[str] = None,
    niveau_scolaire: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    q = db.query(Competence)
    if matiere:
        q = q.filter(Competence.matiere == matiere)
    if niveau_scolaire:
        q = q.filter(Competence.niveau_scolaire == niveau_scolaire)
    total = q.count()
    items = q.order_by(Competence.nom).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.post("/bibliotheque/competences", response_model=CompetenceRead)
def create_competence(
    competence_in: CompetenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_any),
):
    existing = db.query(Competence).filter(Competence.nom == competence_in.nom).first()
    if existing:
        raise HTTPException(status_code=409, detail="Competence already exists")
    comp = Competence(**competence_in.model_dump())
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp


@router.get("/bibliotheque/competences/{competence_id}", response_model=CompetenceRead)
def get_competence(
    competence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    comp = db.query(Competence).filter(Competence.id == competence_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competence not found")
    return comp


@router.delete("/bibliotheque/competences/{competence_id}")
def delete_competence(
    competence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    comp = db.query(Competence).filter(Competence.id == competence_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competence not found")
    db.delete(comp)
    db.commit()
    return {"ok": True}
