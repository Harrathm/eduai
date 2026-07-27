"""Adaptive Pedagogical Pathway — API endpoints.

Endpoints:
- GET  /eleves/{id}/profil-assimilation?chapitre_id=...
- POST /profils-assimilation/{id}/validation  (enseignant)
- GET  /enseignants/{id}/notifications-reorientation
- GET  /notions/{id}/statut-publication
- GET  /eleves/{id}/acces-effectif?matiere_id=...&chapitre_id=...
- POST /packs  (admin)
- POST /scores  (record a score)
- POST /evaluer-reorientation  (trigger evaluation)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db, tenant_unaware
from app.deps import require_admin, require_platform_admin, get_current_user
from app.models import (
    User, Notion, ContenuNotion, ProfilAssimilationEleve,
    NotificationReorientation, HistoriqueScoreEleve,
    ChapterPathway, Matiere, NiveauEtude,
    ActionReorientation, StatutValidationProfil, SourceChangement,
)
from app.schemas import (
    ProfilAssimilationEleveRead, ProfilAssimilationEleveCreate,
    NotificationReorientationRead, StatutPublicationRead,
    NiveauEffectifRead, AccesEffectifRead,
    ContenuNotionRead, ContenuNotionCreate,
    HistoriqueScoreEleveRead, HistoriqueScoreEleveCreate,
    ValidationReorientation,
    NiveauEtudeRead, MatiereRead, ChapterPathwayRead, NotionRead,
    NiveauEtudeCreate, MatiereCreate, ChapterPathwayCreate, NotionCreate,
)
from app.services.adaptive_pathway import (
    statut_publication,
    niveau_effectif,
    evaluer_reorientation,
    contenu_a_servir,
    acces_effectif,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# -------------------------------------------------------------------
# GET /eleves/{id}/profil-assimilation
# -------------------------------------------------------------------
@router.get("/eleves/{eleve_id}/profil-assimilation", response_model=NiveauEffectifRead)
def get_profil_assimilation(
    eleve_id: int,
    chapitre_id: int = Query(..., description="Chapter ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the effective assimilation level for a student on a chapter."""
    # Students can only see their own profile; teachers/admins can see any
    if current_user.role == "student" and current_user.id != eleve_id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    result = niveau_effectif(eleve_id, chapitre_id, db)
    return result


# -------------------------------------------------------------------
# POST /profils-assimilation  (create override)
# -------------------------------------------------------------------
@router.post("/profils-assimilation", response_model=ProfilAssimilationEleveRead)
def create_profil_assimilation(
    profil_in: ProfilAssimilationEleveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an assimilation profile override (teacher/admin only)."""
    if current_user.role not in ("teacher", "admin_school", "super_admin", "pedagogical_admin", "pedagogical_lead"):
        raise HTTPException(status_code=403, detail="Seul un enseignant ou admin peut créer un profil")

    profil = ProfilAssimilationEleve(
        eleve_id=profil_in.eleve_id,
        chapitre_id=profil_in.chapitre_id,
        niveau_assimilation_courant=profil_in.niveau_assimilation_courant,
        source_changement=SourceChangement.OVERRIDE_ENSEIGNANT.value,
        score_declencheur=profil_in.score_declencheur,
        statut_validation=StatutValidationProfil.CONFIRME_ENSEIGNANT.value,
    )
    db.add(profil)
    db.commit()
    db.refresh(profil)
    return profil


# -------------------------------------------------------------------
# POST /profils-assimilation/{id}/validation
# -------------------------------------------------------------------
@router.post("/profils-assimilation/{profil_id}/validation", response_model=ProfilAssimilationEleveRead)
def valider_reorientation(
    profil_id: int,
    validation: ValidationReorientation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Confirm or annul a reorientation (teacher only)."""
    if current_user.role not in ("teacher", "admin_school", "super_admin"):
        raise HTTPException(status_code=403, detail="Seul un enseignant ou admin peut valider")

    profil = db.query(ProfilAssimilationEleve).filter(ProfilAssimilationEleve.id == profil_id).first()
    if not profil:
        raise HTTPException(status_code=404, detail="Profil non trouvé")

    if validation.action == "confirme":
        profil.statut_validation = StatutValidationProfil.CONFIRME_ENSEIGNANT.value
        # Update notification
        notif = db.query(NotificationReorientation).filter(
            NotificationReorientation.profil_assimilation_id == profil_id,
            NotificationReorientation.action_prise == ActionReorientation.AUCUNE.value,
        ).first()
        if notif:
            notif.action_prise = ActionReorientation.CONFIRME.value
    elif validation.action == "annule":
        profil.statut_validation = StatutValidationProfil.ANNULE_ENSEIGNANT.value
        notif = db.query(NotificationReorientation).filter(
            NotificationReorientation.profil_assimilation_id == profil_id,
            NotificationReorientation.action_prise == ActionReorientation.AUCUNE.value,
        ).first()
        if notif:
            notif.action_prise = ActionReorientation.ANNULE.value
    else:
        raise HTTPException(status_code=400, detail="Action invalide: 'confirme' ou 'annule' attendu")

    db.commit()
    db.refresh(profil)
    return profil


# -------------------------------------------------------------------
# GET /enseignants/{id}/notifications-reorientation
# -------------------------------------------------------------------
@router.get("/enseignants/{enseignant_id}/notifications-reorientation",
            response_model=list[NotificationReorientationRead])
def get_notifications_reorientation(
    enseignant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pending reorientation notifications for a teacher."""
    if current_user.role not in ("teacher", "admin_school", "super_admin") and current_user.id != enseignant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    notifications = db.query(NotificationReorientation).filter(
        NotificationReorientation.enseignant_id == enseignant_id,
        NotificationReorientation.action_prise == ActionReorientation.AUCUNE.value,
    ).order_by(NotificationReorientation.date_notification.desc()).all()

    return notifications


# -------------------------------------------------------------------
# GET /notions/{id}/statut-publication
# -------------------------------------------------------------------
@router.get("/notions/{notion_id}/statut-publication", response_model=StatutPublicationRead)
def get_statut_publication(
    notion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get publication status + missing levels for a notion (pedagogical admin)."""
    notion = db.query(Notion).filter(Notion.id == notion_id).first()
    if not notion:
        raise HTTPException(status_code=404, detail="Notion non trouvée")

    result = statut_publication(notion_id, db)
    return result


# -------------------------------------------------------------------
# GET /eleves/{id}/acces-effectif
# -------------------------------------------------------------------
@router.get("/eleves/{eleve_id}/acces-effectif", response_model=AccesEffectifRead)
def get_acces_effectif(
    eleve_id: int,
    matiere_id: int = Query(..., description="Matiere ID"),
    chapitre_id: int = Query(..., description="Chapter ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve dynamic effective access for a student."""
    if current_user.role == "student" and current_user.id != eleve_id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    result = acces_effectif(eleve_id, matiere_id, chapitre_id, db)
    return result


# -------------------------------------------------------------------
# POST /scores  (record a score — triggers reorientation evaluation)
# -------------------------------------------------------------------
@router.post("/scores", response_model=HistoriqueScoreEleveRead)
def record_score(
    score_in: HistoriqueScoreEleveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a score for a student on a chapter. Auto-evaluates reorientation."""
    if current_user.role not in ("teacher", "admin_school", "super_admin",
                                  "student") and current_user.id != score_in.eleve_id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Resolve enseignant_id for notification (if teacher is recording)
    enseignant_id = None
    if current_user.role == "teacher":
        enseignant_id = current_user.id

    historique = HistoriqueScoreEleve(
        eleve_id=score_in.eleve_id,
        chapitre_id=score_in.chapitre_id,
        quiz_id=score_in.quiz_id,
        score=score_in.score,
    )
    db.add(historique)
    db.commit()
    db.refresh(historique)

    # Auto-evaluate reorientation (fire and forget)
    try:
        evaluer_reorientation(
            score_in.eleve_id,
            score_in.chapitre_id,
            db,
            enseignant_id=enseignant_id,
        )
    except Exception as e:
        logger.warning(f"Reorientation evaluation failed: {e}")

    return historique


# -------------------------------------------------------------------
# POST /evaluer-reorientation  (manual trigger)
# -------------------------------------------------------------------
@router.post("/evaluer-reorientation")
def trigger_evaluer_reorientation(
    eleve_id: int = Query(...),
    chapitre_id: int = Query(...),
    enseignant_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger reorientation evaluation for a student/chapter."""
    if current_user.role not in ("teacher", "admin_school", "super_admin", "pedagogical_admin"):
        raise HTTPException(status_code=403, detail="Accès refusé")

    result = evaluer_reorientation(eleve_id, chapitre_id, db, enseignant_id=enseignant_id)
    if result is None:
        return {"message": "Aucune reorientation nécessaire", "reoriented": False}
    return {"message": "Réorientation appliquée", "reoriented": True, **result}


# -------------------------------------------------------------------
# GET /notions/{id}/contenu  (serve content)
# -------------------------------------------------------------------
@router.get("/notions/{notion_id}/contenu")
def get_contenu_a_servir(
    notion_id: int,
    eleve_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the content to serve for a notion, given the student's level."""
    if current_user.role == "student" and current_user.id != eleve_id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    result = contenu_a_servir(notion_id, eleve_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Aucun contenu disponible pour cette notion")
    return result


# -------------------------------------------------------------------
# Admin CRUD: Niveaux d'étude
# -------------------------------------------------------------------
@router.get("/niveaux-etude", response_model=list[NiveauEtudeRead])
def list_niveaux_etude(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    with tenant_unaware():
        niveaux = db.query(NiveauEtude).order_by(NiveauEtude.ordre).all()
    return niveaux


@router.post("/niveaux-etude", response_model=NiveauEtudeRead)
def create_niveau_etude(
    niveau_in: NiveauEtudeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    niveau = NiveauEtude(nom=niveau_in.nom, ordre=niveau_in.ordre)
    db.add(niveau)
    db.commit()
    db.refresh(niveau)
    return niveau


@router.put("/niveaux-etude/{niveau_id}", response_model=NiveauEtudeRead)
def update_niveau_etude(
    niveau_id: int,
    niveau_in: NiveauEtudeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    niveau = db.query(NiveauEtude).filter(NiveauEtude.id == niveau_id).first()
    if not niveau:
        raise HTTPException(status_code=404, detail="Niveau d'étude non trouvé")
    niveau.nom = niveau_in.nom
    niveau.ordre = niveau_in.ordre
    db.commit()
    db.refresh(niveau)
    return niveau


@router.delete("/niveaux-etude/{niveau_id}")
def delete_niveau_etude(
    niveau_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    niveau = db.query(NiveauEtude).filter(NiveauEtude.id == niveau_id).first()
    if not niveau:
        raise HTTPException(status_code=404, detail="Niveau d'étude non trouvé")
    db.delete(niveau)
    db.commit()
    return {"message": "Niveau d'étude supprimé"}


# -------------------------------------------------------------------
# Admin CRUD: Matieres
# -------------------------------------------------------------------
@router.get("/matieres", response_model=list[MatiereRead])
def list_matieres(
    niveau_etude_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    with tenant_unaware():
        q = db.query(Matiere)
        if niveau_etude_id:
            q = q.filter(Matiere.niveau_etude_id == niveau_etude_id)
        matieres = q.all()
    return matieres


@router.post("/matieres", response_model=MatiereRead)
def create_matiere(
    matiere_in: MatiereCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    matiere = Matiere(niveau_etude_id=matiere_in.niveau_etude_id, nom=matiere_in.nom)
    db.add(matiere)
    db.commit()
    db.refresh(matiere)
    return matiere


@router.put("/matieres/{matiere_id}", response_model=MatiereRead)
def update_matiere(
    matiere_id: int,
    matiere_in: MatiereCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    matiere = db.query(Matiere).filter(Matiere.id == matiere_id).first()
    if not matiere:
        raise HTTPException(status_code=404, detail="Matière non trouvée")
    if matiere_in.niveau_etude_id is not None:
        matiere.niveau_etude_id = matiere_in.niveau_etude_id
    if matiere_in.nom is not None:
        matiere.nom = matiere_in.nom
    if matiere_in.remediation_threshold is not None:
        matiere.remediation_threshold = matiere_in.remediation_threshold
    if matiere_in.standard_threshold is not None:
        matiere.standard_threshold = matiere_in.standard_threshold
    if matiere_in.avance_threshold is not None:
        matiere.avance_threshold = matiere_in.avance_threshold
    db.commit()
    db.refresh(matiere)
    return matiere


@router.delete("/matieres/{matiere_id}")
def delete_matiere(
    matiere_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    matiere = db.query(Matiere).filter(Matiere.id == matiere_id).first()
    if not matiere:
        raise HTTPException(status_code=404, detail="Matière non trouvée")
    db.delete(matiere)
    db.commit()
    return {"message": "Matière supprimée"}


# -------------------------------------------------------------------
# Admin CRUD: Chapters
# -------------------------------------------------------------------
@router.get("/chapter-pathways", response_model=list[ChapterPathwayRead])
def list_chapters(
    matiere_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    with tenant_unaware():
        q = db.query(ChapterPathway)
        if matiere_id:
            q = q.filter(ChapterPathway.matiere_id == matiere_id)
        chapters = q.order_by(ChapterPathway.ordre).all()
    return chapters


@router.post("/chapter-pathways", response_model=ChapterPathwayRead)
def create_chapter(
    chapter_in: ChapterPathwayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    chapter = ChapterPathway(
        matiere_id=chapter_in.matiere_id,
        nom=chapter_in.nom,
        ordre=chapter_in.ordre,
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.put("/chapter-pathways/{chapter_id}", response_model=ChapterPathwayRead)
def update_chapter(
    chapter_id: int,
    chapter_in: ChapterPathwayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    chapter = db.query(ChapterPathway).filter(ChapterPathway.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre non trouvé")
    chapter.matiere_id = chapter_in.matiere_id
    chapter.nom = chapter_in.nom
    chapter.ordre = chapter_in.ordre
    db.commit()
    db.refresh(chapter)
    return chapter


@router.delete("/chapter-pathways/{chapter_id}")
def delete_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    chapter = db.query(ChapterPathway).filter(ChapterPathway.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre non trouvé")
    db.delete(chapter)
    db.commit()
    return {"message": "Chapitre supprimé"}


# -------------------------------------------------------------------
# Admin CRUD: Notions
# -------------------------------------------------------------------
@router.get("/notions-list", response_model=list[NotionRead])
def list_notions(
    chapitre_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    with tenant_unaware():
        q = db.query(Notion)
        if chapitre_id:
            q = q.filter(Notion.chapitre_id == chapitre_id)
        notions = q.order_by(Notion.ordre).all()
    return notions


@router.post("/notions-list", response_model=NotionRead)
def create_notion(
    notion_in: NotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    notion = Notion(
        chapitre_id=notion_in.chapitre_id,
        nom=notion_in.nom,
        ordre=notion_in.ordre,
    )
    db.add(notion)
    db.commit()
    db.refresh(notion)
    return notion


@router.put("/notions-list/{notion_id}", response_model=NotionRead)
def update_notion(
    notion_id: int,
    notion_in: NotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    notion = db.query(Notion).filter(Notion.id == notion_id).first()
    if not notion:
        raise HTTPException(status_code=404, detail="Notion non trouvée")
    notion.chapitre_id = notion_in.chapitre_id
    notion.nom = notion_in.nom
    notion.ordre = notion_in.ordre
    db.commit()
    db.refresh(notion)
    return notion


@router.delete("/notions-list/{notion_id}")
def delete_notion(
    notion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    notion = db.query(Notion).filter(Notion.id == notion_id).first()
    if not notion:
        raise HTTPException(status_code=404, detail="Notion non trouvée")
    db.delete(notion)
    db.commit()
    return {"message": "Notion supprimée"}


# -------------------------------------------------------------------
# Admin CRUD: Contenus
# -------------------------------------------------------------------
@router.get("/contenus", response_model=list[ContenuNotionRead])
def list_contenus(
    notion_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    with tenant_unaware():
        q = db.query(ContenuNotion)
        if notion_id:
            q = q.filter(ContenuNotion.notion_id == notion_id)
        contenus = q.all()
    return contenus


@router.post("/contenus", response_model=ContenuNotionRead)
def create_contenu(
    contenu_in: ContenuNotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    contenu = ContenuNotion(
        notion_id=contenu_in.notion_id,
        niveau_assimilation=contenu_in.niveau_assimilation,
        type_ressource=contenu_in.type_ressource,
        contenu=contenu_in.contenu,
        enseignant_id=contenu_in.enseignant_id,
        statut_pedagogique=contenu_in.statut_pedagogique,
    )
    db.add(contenu)
    db.commit()
    db.refresh(contenu)
    return contenu


@router.put("/contenus/{contenu_id}", response_model=ContenuNotionRead)
def update_contenu(
    contenu_id: int,
    contenu_in: ContenuNotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    contenu = db.query(ContenuNotion).filter(ContenuNotion.id == contenu_id).first()
    if not contenu:
        raise HTTPException(status_code=404, detail="Contenu non trouvé")
    contenu.notion_id = contenu_in.notion_id
    contenu.niveau_assimilation = contenu_in.niveau_assimilation
    contenu.type_ressource = contenu_in.type_ressource
    contenu.contenu = contenu_in.contenu
    contenu.enseignant_id = contenu_in.enseignant_id
    contenu.statut_pedagogique = contenu_in.statut_pedagogique
    db.commit()
    db.refresh(contenu)
    return contenu


@router.delete("/contenus/{contenu_id}")
def delete_contenu(
    contenu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    contenu = db.query(ContenuNotion).filter(ContenuNotion.id == contenu_id).first()
    if not contenu:
        raise HTTPException(status_code=404, detail="Contenu non trouvé")
    db.delete(contenu)
    db.commit()
    return {"message": "Contenu supprimé"}


# ============================================================
# PATHWAY CATALOG + PURCHASE + PROGRESSION
# ============================================================

from datetime import datetime, timezone, timedelta
from app.models import (
    StudyPack, PackPurchase, PackPurchaseStatus, PackStatus, PurchaserType,
    Transaction, TransactionType, Currency, School,
    Progress, Lesson, Module,
)


@router.get("/catalog")
def pathway_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List available pathways (NiveauEtude + Matieres) with pack info and access status."""
    with tenant_unaware():
        niveaux = db.query(NiveauEtude).order_by(NiveauEtude.ordre).all()
        all_matieres = db.query(Matiere).all()
        all_chapters = db.query(ChapterPathway).all()
        all_notions = db.query(Notion).all()
        all_packs = db.query(StudyPack).filter(StudyPack.status == PackStatus.PUBLISHED.value).all()

    # Check what the student already has access to
    now = datetime.now(timezone.utc)
    active_pack_niveaux = set()
    active_pack_purchases = []
    if current_user.school_id:
        school_packs = db.query(PackPurchase).filter(
            PackPurchase.school_id == current_user.school_id,
            PackPurchase.purchaser_type == PurchaserType.SCHOOL.value,
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
        ).all()
        for sp in school_packs:
            pack = db.query(StudyPack).filter(StudyPack.id == sp.pack_id).first()
            if pack:
                active_pack_niveaux.add(pack.niveau_scolaire)
                active_pack_purchases.append(sp)

    student_packs = db.query(PackPurchase).filter(
        PackPurchase.student_id == current_user.id,
        PackPurchase.purchaser_type == PurchaserType.STUDENT.value,
        PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
        PackPurchase.valid_until > now,
    ).all()
    for sp in student_packs:
        pack = db.query(StudyPack).filter(StudyPack.id == sp.pack_id).first()
        if pack:
            active_pack_niveaux.add(pack.niveau_scolaire)
            active_pack_purchases.append(sp)

    # Build pathway tree
    result = []
    for niveau in niveaux:
        matieres_data = []
        for matiere in all_matieres:
            if matiere.niveau_etude_id != niveau.id:
                continue
            chapters_data = []
            for ch in all_chapters:
                if ch.matiere_id != matiere.id:
                    continue
                notions_count = len([n for n in all_notions if n.chapitre_id == ch.id])
                chapters_data.append({
                    "id": ch.id,
                    "nom": ch.nom,
                    "ordre": ch.ordre,
                    "notions_count": notions_count,
                })
            matieres_data.append({
                "id": matiere.id,
                "nom": matiere.nom,
                "chapters_count": len(chapters_data),
                "chapters": chapters_data,
            })

        # Find matching pack
        matching_pack = None
        for p in all_packs:
            if p.niveau_scolaire == niveau.nom:
                matching_pack = p
                break

        has_access = niveau.nom in active_pack_niveaux
        purchase = None
        for pp in active_pack_purchases:
            pack = db.query(StudyPack).filter(StudyPack.id == pp.pack_id).first()
            if pack and pack.niveau_scolaire == niveau.nom:
                purchase = {
                    "valid_until": pp.valid_until.isoformat(),
                    "purchaser_type": pp.purchaser_type,
                }
                break

        result.append({
            "niveau": {
                "id": niveau.id,
                "nom": niveau.nom,
                "ordre": niveau.ordre,
            },
            "matieres": matieres_data,
            "pack": {
                "id": matching_pack.id if matching_pack else None,
                "name": matching_pack.name if matching_pack else None,
                "price": matching_pack.price if matching_pack else None,
                "currency": matching_pack.currency if matching_pack else "TND",
            } if matching_pack else None,
            "has_access": has_access,
            "purchase": purchase,
        })

    return result


@router.get("/mon-parcours")
def mon_parcours(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the student's full pathway with progression per chapter."""
    now = datetime.now(timezone.utc)

    # Find active packs
    active_niveaux = set()
    if current_user.school_id:
        school_packs = db.query(PackPurchase).filter(
            PackPurchase.school_id == current_user.school_id,
            PackPurchase.purchaser_type == PurchaserType.SCHOOL.value,
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
        ).all()
        for sp in school_packs:
            pack = db.query(StudyPack).filter(StudyPack.id == sp.pack_id).first()
            if pack:
                active_niveaux.add(pack.niveau_scolaire)

    student_packs = db.query(PackPurchase).filter(
        PackPurchase.student_id == current_user.id,
        PackPurchase.purchaser_type == PurchaserType.STUDENT.value,
        PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
        PackPurchase.valid_until > now,
    ).all()
    for sp in student_packs:
        pack = db.query(StudyPack).filter(StudyPack.id == sp.pack_id).first()
        if pack:
            active_niveaux.add(pack.niveau_scolaire)

    if not active_niveaux:
        return {"message": "Aucun pack actif. Achetez un pack pour accéder à votre parcours.", "niveaux": []}

    with tenant_unaware():
        niveaux = db.query(NiveauEtude).filter(NiveauEtude.nom.in_(active_niveaux)).order_by(NiveauEtude.ordre).all()
        all_matieres = db.query(Matiere).all()
        all_chapters = db.query(ChapterPathway).all()
        all_notions = db.query(Notion).all()

    # Get student profiles
    profiles = db.query(ProfilAssimilationEleve).filter(
        ProfilAssimilationEleve.eleve_id == current_user.id,
    ).all()
    profile_map = {}
    for p in profiles:
        profile_map[p.chapitre_id] = p

    # Get student scores
    scores = db.query(HistoriqueScoreEleve).filter(
        HistoriqueScoreEleve.eleve_id == current_user.id,
    ).all()
    score_map = {}
    for s in scores:
        score_map.setdefault(s.chapitre_id, []).append(s.score)

    # Get student lesson progress
    progress_records = db.query(Progress).filter(
        Progress.user_id == current_user.id,
    ).all()
    progress_map = {}
    for pr in progress_records:
        # Find which chapter this lesson belongs to
        lesson = db.query(Lesson).filter(Lesson.id == pr.lesson_id).first()
        if lesson:
            module = db.query(Module).filter(Module.id == lesson.module_id).first()
            if module:
                # Map course to chapter via matiere/category
                progress_map.setdefault(module.id, []).append(pr)

    result = []
    for niveau in niveaux:
        matieres_data = []
        for matiere in all_matieres:
            if matiere.niveau_etude_id != niveau.id:
                continue
            chapters_data = []
            for ch in all_chapters:
                if ch.matiere_id != matiere.id:
                    continue
                notions = [n for n in all_notions if n.chapitre_id == ch.id]
                profile = profile_map.get(ch.id)
                chap_scores = score_map.get(ch.id, [])
                avg_score = sum(chap_scores) / len(chap_scores) if chap_scores else None

                # Determine chapter status
                if profile:
                    if profile.statut_validation == "annule_enseignant":
                        status = "annule"
                    elif profile.niveau_assimilation_courant:
                        status = "en_cours"
                    else:
                        status = "a_commencer"
                else:
                    status = "a_commencer"

                notions_data = []
                for notion in notions:
                    has_content = db.query(ContenuNotion).filter(
                        ContenuNotion.notion_id == notion.id,
                        ContenuNotion.statut_pedagogique == "a",
                    ).count() > 0
                    notions_data.append({
                        "id": notion.id,
                        "nom": notion.nom,
                        "ordre": notion.ordre,
                        "has_content": has_content,
                    })

                chapters_data.append({
                    "id": ch.id,
                    "nom": ch.nom,
                    "ordre": ch.ordre,
                    "status": status,
                    "niveau_assimilation": profile.niveau_assimilation_courant if profile else None,
                    "score_moyen": round(avg_score * 100, 1) if avg_score is not None else None,
                    "scores_count": len(chap_scores),
                    "notions_count": len(notions),
                    "notions": notions_data,
                })

            matieres_data.append({
                "id": matiere.id,
                "nom": matiere.nom,
                "chapters_count": len(chapters_data),
                "chapters": chapters_data,
            })

        result.append({
            "niveau": {"id": niveau.id, "nom": niveau.nom},
            "matieres": matieres_data,
        })

    return {"niveaux": result}


@router.post("/enroll-pathway")
def enroll_pathway(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enroll in a pathway after pack purchase — creates initial profiles for all chapters."""
    niveau_id = body.get("niveau_id")
    if not niveau_id:
        raise HTTPException(status_code=400, detail="niveau_id requis")

    # Verify student has active pack for this niveau
    niveau = db.query(NiveauEtude).filter(NiveauEtude.id == niveau_id).first()
    if not niveau:
        raise HTTPException(status_code=404, detail="Niveau non trouvé")

    now = datetime.now(timezone.utc)
    has_access = False

    # Check school pack
    if current_user.school_id:
        school_pack = db.query(PackPurchase).filter(
            PackPurchase.school_id == current_user.school_id,
            PackPurchase.purchaser_type == PurchaserType.SCHOOL.value,
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
        ).join(StudyPack).filter(StudyPack.niveau_scolaire == niveau.nom).first()
        if school_pack:
            has_access = True

    # Check student pack
    if not has_access:
        student_pack = db.query(PackPurchase).filter(
            PackPurchase.student_id == current_user.id,
            PackPurchase.purchaser_type == PurchaserType.STUDENT.value,
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
        ).join(StudyPack).filter(StudyPack.niveau_scolaire == niveau.nom).first()
        if student_pack:
            has_access = True

    if not has_access:
        raise HTTPException(status_code=403, detail="Vous n'avez pas de pack actif pour ce niveau")

    # Find all chapters for this niveau
    matieres = db.query(Matiere).filter(Matiere.niveau_etude_id == niveau_id).all()
    matiere_ids = [m.id for m in matieres]
    chapters = db.query(ChapterPathway).filter(ChapterPathway.matiere_id.in_(matiere_ids)).all()

    # Create profiles for chapters without one
    created = 0
    for ch in chapters:
        existing = db.query(ProfilAssimilationEleve).filter(
            ProfilAssimilationEleve.eleve_id == current_user.id,
            ProfilAssimilationEleve.chapitre_id == ch.id,
        ).first()
        if not existing:
            profil = ProfilAssimilationEleve(
                eleve_id=current_user.id,
                chapitre_id=ch.id,
                niveau_assimilation_courant="standard",
                source_changement=SourceChangement.TEST_INITIAL.value,
                statut_validation=StatutValidationProfil.AUTO_APPLIQUE.value,
            )
            db.add(profil)
            created += 1

    db.commit()

    return {
        "message": f"Parcours inscrit. {created} chapitre(s) initialisé(s).",
        "niveau": niveau.nom,
        "chapters_initialized": created,
        "total_chapters": len(chapters),
    }


# ============================================================
# RBAC PÉDAGOGIQUE — SPÉCIALITÉS & RESPONSABLES
# ============================================================

from app.models import (
    SpecialitePedagogique, SpecialitePedagogiqueMatiere, ResponsablePedagogique,
)


@router.get("/specialites-pedagogiques")
def list_specialites(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """Liste les spécialités pédagogiques de l'école."""
    specs = db.query(SpecialitePedagogique).filter(
        SpecialitePedagogique.ecole_id == current_user.school_id
    ).all() if current_user.school_id else db.query(SpecialitePedagogique).all()

    result = []
    for s in specs:
        matiere_ids = [sm.matiere_id for sm in db.query(SpecialitePedagogiqueMatiere).filter(
            SpecialitePedagogiqueMatiere.specialite_id == s.id
        ).all()]
        result.append({
            "id": s.id,
            "nom": s.nom,
            "cycle_scolaire": s.cycle_scolaire,
            "ecole_id": s.ecole_id,
            "matiere_ids": matiere_ids,
        })
    return result


@router.post("/specialites-pedagogiques")
def create_specialite(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """Crée une spécialité pédagogique."""
    spec = SpecialitePedagogique(
        ecole_id=current_user.school_id or body.get("ecole_id"),
        nom=body["nom"],
        cycle_scolaire=body.get("cycle_scolaire", "2eme_cycle"),
    )
    db.add(spec)
    db.flush()

    for matiere_id in body.get("matiere_ids", []):
        db.add(SpecialitePedagogiqueMatiere(specialite_id=spec.id, matiere_id=matiere_id))

    db.commit()
    db.refresh(spec)
    return {"id": spec.id, "nom": spec.nom, "message": "Spécialité créée"}


@router.post("/responsables-pedagogiques")
def assign_responsable(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """Assigne un responsable pédagogique à une spécialité."""
    resp = ResponsablePedagogique(
        user_id=body["user_id"],
        specialite_id=body["specialite_id"],
    )
    db.add(resp)
    db.flush()

    # Ajouter les niveaux_etude_scope
    from app.models import NiveauEtude
    for niv_id in body.get("niveaux_etude_ids", []):
        niv = db.query(NiveauEtude).filter(NiveauEtude.id == niv_id).first()
        if niv:
            resp.niveaux_etude_scope.append(niv)

    db.commit()
    db.refresh(resp)
    return {"id": resp.id, "message": "Responsable assigné"}


@router.get("/responsables-pedagogiques/{user_id}/contenus")
def get_responsable_contenus(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne les contenus filtrés par spécialité et niveaux_etude_scope du responsable."""
    from app.services.adaptive_pathway import get_contenus_for_responsable
    contenus = get_contenus_for_responsable(user_id, db)
    return [
        {
            "id": c.id,
            "notion_id": c.notion_id,
            "niveau_assimilation": c.niveau_assimilation,
            "type_ressource": c.type_ressource,
            "statut_pedagogique": c.statut_pedagogique,
            "statut_validation_pedagogique": c.statut_validation_pedagogique,
            "enseignant_id": c.enseignant_id,
        }
        for c in contenus
    ]


@router.post("/contenus-notion/{contenu_id}/valider")
def valider_contenu_endpoint(
    contenu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Valide un contenu par un responsable pédagogique."""
    contenu = db.query(ContenuNotion).filter(ContenuNotion.id == contenu_id).first()
    if not contenu:
        raise HTTPException(status_code=404, detail="Contenu non trouvé")

    from app.services.adaptive_pathway import valider_contenu, contenu_visible as check_contenu_visible
    if not check_contenu_visible(current_user.id, contenu, db):
        raise HTTPException(status_code=403, detail="Ce contenu n'est pas dans votre périmètre pédagogique")

    valider_contenu(contenu, current_user.id, db)
    return {"message": "Contenu validé", "statut_validation": "valide"}


@router.post("/contenus-notion/{contenu_id}/rejeter")
def rejeter_contenu_endpoint(
    contenu_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rejette un contenu avec commentaire."""
    contenu = db.query(ContenuNotion).filter(ContenuNotion.id == contenu_id).first()
    if not contenu:
        raise HTTPException(status_code=404, detail="Contenu non trouvé")

    commentaire = body.get("commentaire", "")
    if not commentaire:
        raise HTTPException(status_code=400, detail="Un commentaire de rejet est obligatoire")

    from app.services.adaptive_pathway import rejeter_contenu, contenu_visible as check_contenu_visible
    if not check_contenu_visible(current_user.id, contenu, db):
        raise HTTPException(status_code=403, detail="Ce contenu n'est pas dans votre périmètre pédagogique")

    rejeter_contenu(contenu, current_user.id, commentaire, db)
    return {"message": "Contenu rejeté", "statut_validation": "rejete"}
