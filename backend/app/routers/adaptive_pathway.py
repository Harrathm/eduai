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
