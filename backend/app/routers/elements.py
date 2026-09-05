"""
Module A — Elements Pédagogiques CRUD + Workflow + Promotion
"""
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.deps import (
    set_tenant_context,
    check_school_access,
    require_teacher_or_admin,
    require_admin,
    require_super_admin,
    require_pedagogical_any,
    get_user_role,
)
from app.models import (
    User, ElementPedagogique, ElementTexte, ElementVideo, ElementImage,
    ElementQuiz, ElementPdf, ContentWorkflow, ContentPromotion, Parcours,
)
from app.schemas import (
    ElementPedagogiqueCreate, ElementPedagogiqueRead, ElementPedagogiqueUpdate,
    ElementTexteCreate, ElementTexteRead,
    ElementVideoCreate, ElementVideoRead,
    ElementImageCreate, ElementImageRead,
    ElementQuizCreate, ElementQuizRead,
    ElementPdfCreate, ElementPdfRead,
    ContentWorkflowRead, ContentPromotionRead,
)

router = APIRouter(tags=["Module A - Elements"])

utcnow = lambda: datetime.now(timezone.utc)


def _check_element_school_scope(element: ElementPedagogique, current_user: User, db: Session):
    """For pedagogical_lead, ensure element author belongs to the lead's school."""
    from app.deps import get_user_role
    from app.db import tenant_unaware
    role = get_user_role(current_user)
    if role == "pedagogical_lead" and element.auteur_id:
        with tenant_unaware():
            author = db.query(User).filter(User.id == element.auteur_id).first()
        if author and author.school_id and author.school_id != current_user.school_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot operate on elements from another school",
            )

# Workflow valid transitions
VALID_TRANSITIONS = {
    "brouillon": "en_review",
    "brouillon_ia": "en_review",
    "en_review": ["publie", "rejete"],
    "rejete": "en_review",
    "publie": "brouillon",
}


def _require_element_writable(element: ElementPedagogique, current_user: User):
    """Block subtype writes on published elements (except admins who must demote first)."""
    role = get_user_role(current_user)
    is_admin = role in ("super_admin", "pedagogical_admin")
    if element.statut == "publie" and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify content on a published element. Demote it to draft first.",
        )


# ============================================================
# ELEMENTS PEDAGOGIQUES
# ============================================================

@router.get("/elements")
def list_elements(
    skip: int = 0,
    limit: int = 20,
    type: Optional[str] = None,
    statut: Optional[str] = None,
    matiere_id: Optional[int] = None,
    lecon_id: Optional[int] = None,
    est_global: Optional[bool] = None,
    est_libre: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    q = db.query(ElementPedagogique)

    if type:
        q = q.filter(ElementPedagogique.type == type)
    if statut:
        q = q.filter(ElementPedagogique.statut == statut)
    if matiere_id:
        q = q.filter(ElementPedagogique.matiere_id == matiere_id)
    if lecon_id:
        q = q.filter(ElementPedagogique.lecon_id == lecon_id)
    if est_global is not None:
        q = q.filter(ElementPedagogique.est_global == est_global)
    if est_libre is not None:
        q = q.filter(ElementPedagogique.est_libre == est_libre)
    if search:
        q = q.filter(ElementPedagogique.titre.ilike(f"%{search}%"))

    total = q.count()
    items = q.order_by(ElementPedagogique.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.post("/elements", response_model=ElementPedagogiqueRead)
def create_element(
    element_in: ElementPedagogiqueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    if not element_in.lecon_id and not element_in.paragraphe_id:
        raise HTTPException(status_code=400, detail="Either lecon_id or paragraphe_id is required")
    if element_in.lecon_id and element_in.paragraphe_id:
        raise HTTPException(status_code=400, detail="Only one of lecon_id or paragraphe_id can be set")

    element = ElementPedagogique(
        **element_in.model_dump(),
        auteur_id=current_user.id,
        statut="brouillon",
    )
    db.add(element)
    db.commit()
    db.refresh(element)
    return element


@router.get("/elements/{element_id}", response_model=ElementPedagogiqueRead)
def get_element(
    element_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")

    from app.deps import get_user_role
    role = get_user_role(current_user)
    is_staff = role in ("super_admin", "pedagogical_admin", "pedagogical_lead", "admin_school")
    is_author = element.auteur_id == current_user.id

    if not is_staff:
        if role in ("student", "user"):
            if element.statut != "publie":
                raise HTTPException(status_code=403, detail="Access denied")
        elif role == "teacher":
            if element.statut != "publie" and not is_author:
                raise HTTPException(status_code=403, detail="Access denied")

    return element


@router.put("/elements/{element_id}", response_model=ElementPedagogiqueRead)
def update_element(
    element_id: int,
    element_update: ElementPedagogiqueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    is_admin = current_user.role in ("admin_school", "super_admin", "pedagogical_admin")
    is_author = element.auteur_id == current_user.id
    if not is_admin and not is_author:
        raise HTTPException(status_code=403, detail="Only the author or an admin can modify")
    if is_author and not is_admin:
        if element.statut not in ("brouillon", "brouillon_ia", "rejete"):
            raise HTTPException(status_code=403, detail=f"Cannot edit element in '{element.statut}' status. Only drafts, AI drafts, and rejected elements can be edited.")
    for field, value in element_update.model_dump(exclude_unset=True).items():
        setattr(element, field, value)
    element.updated_at = utcnow()
    db.commit()
    db.refresh(element)
    return element


@router.patch("/elements/{element_id}", response_model=ElementPedagogiqueRead)
def patch_element(
    element_id: int,
    element_update: ElementPedagogiqueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    is_admin = current_user.role in ("admin_school", "super_admin", "pedagogical_admin")
    is_author = element.auteur_id == current_user.id
    if not is_admin and not is_author:
        raise HTTPException(status_code=403, detail="Only the author or an admin can modify")
    if is_author and not is_admin:
        if element.statut not in ("brouillon", "brouillon_ia", "rejete"):
            raise HTTPException(status_code=403, detail=f"Cannot edit element in '{element.statut}' status. Only drafts, AI drafts, and rejected elements can be edited.")
    for field, value in element_update.model_dump(exclude_unset=True).items():
        setattr(element, field, value)
    element.updated_at = utcnow()
    db.commit()
    db.refresh(element)
    return element


@router.delete("/elements/{element_id}")
def delete_element(
    element_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    db.delete(element)
    db.commit()
    return {"ok": True}


# ============================================================
# WORKFLOW (submit / validate / reject)
# ============================================================

def _transition_statut(element: ElementPedagogique, nouveau_statut: str, auteur_id: int, commentaires: str, db: Session):
    ancien = element.statut
    element.statut = nouveau_statut
    element.updated_at = utcnow()
    wf = ContentWorkflow(
        element_id=element.id,
        ancien_statut=ancien,
        nouveau_statut=nouveau_statut,
        commentaires=commentaires,
        auteur_id=auteur_id,
    )
    db.add(wf)


@router.post("/elements/{element_id}/submit", response_model=ElementPedagogiqueRead)
def submit_element(
    element_id: int,
    commentaires: str = Body("", embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    if element.auteur_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the author can submit")
    if element.statut not in ("brouillon", "brouillon_ia", "rejete"):
        raise HTTPException(status_code=400, detail=f"Cannot submit from status '{element.statut}'")

    _transition_statut(element, "en_review", current_user.id, commentaires or "Soumis pour review", db)
    db.commit()
    db.refresh(element)
    return element


@router.post("/elements/{element_id}/validate", response_model=ElementPedagogiqueRead)
def validate_element(
    element_id: int,
    commentaires: str = Body("", embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_any),
):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    _check_element_school_scope(element, current_user, db)
    if element.statut not in ("en_review", "brouillon_ia"):
        raise HTTPException(status_code=400, detail=f"Cannot validate from status '{element.statut}'")

    _transition_statut(element, "publie", current_user.id, commentaires or "Validé", db)
    db.commit()
    db.refresh(element)
    return element


@router.post("/elements/{element_id}/reject", response_model=ElementPedagogiqueRead)
def reject_element(
    element_id: int,
    commentaires: str = Body("Non conforme", embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_any),
):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    _check_element_school_scope(element, current_user, db)
    if element.statut not in ("en_review", "brouillon_ia"):
        raise HTTPException(status_code=400, detail=f"Cannot reject from status '{element.statut}'")

    _transition_statut(element, "rejete", current_user.id, commentaires, db)
    db.commit()
    db.refresh(element)
    return element


@router.get("/elements/{element_id}/workflow")
def list_workflow(
    element_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    items = db.query(ContentWorkflow).filter(
        ContentWorkflow.element_id == element_id
    ).order_by(ContentWorkflow.created_at).all()
    return {"total": len(items), "items": items}


# ============================================================
# PROMOTION LOCALE → GLOBALE
# ============================================================

def _copy_subtype_content(db: Session, source: ElementPedagogique, target: ElementPedagogique) -> None:
    """Duplicate the subtype payload (texte/video/image/quiz/pdf) onto the global copy."""
    if source.type == "texte":
        src = db.query(ElementTexte).filter(ElementTexte.element_id == source.id).first()
        if src:
            db.add(ElementTexte(element_id=target.id, corps=src.corps))
    elif source.type == "video":
        src = db.query(ElementVideo).filter(ElementVideo.element_id == source.id).first()
        if src:
            db.add(ElementVideo(
                element_id=target.id, url=src.url,
                duree_secondes=src.duree_secondes, thumbnail_url=src.thumbnail_url,
            ))
    elif source.type == "image":
        src = db.query(ElementImage).filter(ElementImage.element_id == source.id).first()
        if src:
            db.add(ElementImage(element_id=target.id, url=src.url, alt_text=src.alt_text))
    elif source.type == "quiz":
        src = db.query(ElementQuiz).filter(ElementQuiz.element_id == source.id).first()
        if src:
            db.add(ElementQuiz(
                element_id=target.id, questions_json=src.questions_json,
                score_reussite=src.score_reussite,
            ))
    elif source.type == "pdf":
        src = db.query(ElementPdf).filter(ElementPdf.element_id == source.id).first()
        if src:
            db.add(ElementPdf(
                element_id=target.id, url=src.url,
                pages=src.pages, taille_octets=src.taille_octets,
            ))


@router.post("/elements/{element_id}/promote-global", response_model=ElementPedagogiqueRead)
def promote_global(
    element_id: int,
    parcours_destination_id: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_any),
):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    _check_element_school_scope(element, current_user, db)
    if element.statut != "publie":
        raise HTTPException(status_code=400, detail="Only published elements can be promoted")

    import json
    snapshot = {
        "titre": element.titre,
        "type": element.type,
        "description": element.description,
        "statut": element.statut,
        "difficulte": element.difficulte,
        "metadonnees": element.metadonnees,
    }

    global_copy = ElementPedagogique(
        type=element.type,
        titre=element.titre,
        description=element.description,
        matiere_id=element.matiere_id,
        niveau_etude_id=element.niveau_etude_id,
        difficulte=element.difficulte,
        metadonnees=json.loads(json.dumps(element.metadonnees)) if element.metadonnees else None,
        auteur_id=current_user.id,
        statut="publie",
        est_global=True,
        est_libre=element.est_libre,
    )
    db.add(global_copy)
    db.flush()

    _copy_subtype_content(db, element, global_copy)

    promotion = ContentPromotion(
        element_source_id=element.id,
        element_promoted_id=global_copy.id,
        parcours_destination_id=parcours_destination_id,
        snapshot_json=snapshot,
        effectuee_par_id=current_user.id,
    )
    db.add(promotion)

    db.commit()
    db.refresh(global_copy)
    return global_copy


# ============================================================
# SUBTYPE CONTENT (texte, video, image, quiz, pdf)
# ============================================================

@router.get("/elements/{element_id}/texte", response_model=ElementTexteRead)
def get_texte(element_id: int, db: Session = Depends(get_db), current_user: User = Depends(set_tenant_context)):
    item = db.query(ElementTexte).filter(ElementTexte.element_id == element_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Texte not found")
    return item


@router.post("/elements/{element_id}/texte", response_model=ElementTexteRead)
def create_texte(element_id: int, body: ElementTexteCreate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_or_admin)):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    _require_element_writable(element, current_user)
    existing = db.query(ElementTexte).filter(ElementTexte.element_id == element_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Texte already exists for this element")
    item = ElementTexte(element_id=element_id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/elements/{element_id}/video", response_model=ElementVideoRead)
def get_video(element_id: int, db: Session = Depends(get_db), current_user: User = Depends(set_tenant_context)):
    item = db.query(ElementVideo).filter(ElementVideo.element_id == element_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Video not found")
    return item


@router.post("/elements/{element_id}/video", response_model=ElementVideoRead)
def create_video(element_id: int, body: ElementVideoCreate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_or_admin)):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    _require_element_writable(element, current_user)
    existing = db.query(ElementVideo).filter(ElementVideo.element_id == element_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Video already exists for this element")
    item = ElementVideo(element_id=element_id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/elements/{element_id}/image", response_model=ElementImageRead)
def get_image(element_id: int, db: Session = Depends(get_db), current_user: User = Depends(set_tenant_context)):
    item = db.query(ElementImage).filter(ElementImage.element_id == element_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Image not found")
    return item


@router.post("/elements/{element_id}/image", response_model=ElementImageRead)
def create_image(element_id: int, body: ElementImageCreate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_or_admin)):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    _require_element_writable(element, current_user)
    existing = db.query(ElementImage).filter(ElementImage.element_id == element_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Image already exists for this element")
    item = ElementImage(element_id=element_id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/elements/{element_id}/quiz", response_model=ElementQuizRead)
def get_quiz(element_id: int, db: Session = Depends(get_db), current_user: User = Depends(set_tenant_context)):
    item = db.query(ElementQuiz).filter(ElementQuiz.element_id == element_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return item


@router.post("/elements/{element_id}/quiz", response_model=ElementQuizRead)
def create_quiz(element_id: int, body: ElementQuizCreate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_or_admin)):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    _require_element_writable(element, current_user)
    existing = db.query(ElementQuiz).filter(ElementQuiz.element_id == element_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Quiz already exists for this element")
    item = ElementQuiz(element_id=element_id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/elements/{element_id}/pdf", response_model=ElementPdfRead)
def get_pdf(element_id: int, db: Session = Depends(get_db), current_user: User = Depends(set_tenant_context)):
    item = db.query(ElementPdf).filter(ElementPdf.element_id == element_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="PDF not found")
    return item


@router.post("/elements/{element_id}/pdf", response_model=ElementPdfRead)
def create_pdf(element_id: int, body: ElementPdfCreate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_or_admin)):
    element = db.query(ElementPedagogique).filter(ElementPedagogique.id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    _require_element_writable(element, current_user)
    existing = db.query(ElementPdf).filter(ElementPdf.element_id == element_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="PDF already exists for this element")
    item = ElementPdf(element_id=element_id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
