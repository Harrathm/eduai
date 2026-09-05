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

from app.db.session import get_db, tenant_unaware, _tenant_filter_suppressed
from app.deps import require_admin, require_platform_admin, get_current_user, set_tenant_context
from app.models import (
    User, Notion, ContenuNotion, ProfilAssimilationEleve,
    NotificationReorientation, HistoriqueScoreEleve,
    ChapterPathway, Matiere, NiveauEtude,
    ActionReorientation, StatutValidationProfil, SourceChangement,
    Abonnement, PackDefinition,
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
    current_user: User = Depends(set_tenant_context),
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
    current_user: User = Depends(set_tenant_context),
):
    """Create an assimilation profile override (teacher/admin only)."""
    if current_user.role not in ("teacher", "admin_school", "super_admin", "pedagogical_admin", "pedagogical_lead"):
        raise HTTPException(status_code=403, detail="Seul un enseignant ou admin peut créer un profil")

    # School scope check for teachers: ensure student belongs to same school
    if current_user.role == "teacher" and current_user.school_id:
        student = db.query(User).filter(User.id == profil_in.eleve_id).first()
        if not student or student.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="Cet élève n'appartient pas à votre établissement")

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
    current_user: User = Depends(set_tenant_context),
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
    current_user: User = Depends(set_tenant_context),
):
    """List pending reorientation notifications for a teacher."""
    from app.deps import get_user_role
    role = get_user_role(current_user)
    if current_user.id != enseignant_id and role not in ("admin_school", "super_admin"):
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
    current_user: User = Depends(set_tenant_context),
):
    """Get publication status + missing levels for a notion (teacher/admin only)."""
    from app.deps import get_user_role
    role = get_user_role(current_user)
    if role not in ("teacher", "admin_school", "super_admin", "pedagogical_admin", "pedagogical_lead"):
        raise HTTPException(status_code=403, detail="Seul un enseignant ou admin peut consulter le statut de publication")

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
    current_user: User = Depends(set_tenant_context),
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
    current_user: User = Depends(set_tenant_context),
):
    """Record a score for a student on a chapter. Auto-evaluates reorientation."""
    # Teachers/admins can record scores for any student.
    # Students can ONLY record scores for themselves.
    if current_user.role == "student":
        if current_user.id != score_in.eleve_id:
            raise HTTPException(status_code=403, detail="Un étudiant ne peut enregistrer des scores que pour lui-même")
    elif current_user.role not in ("teacher", "admin_school", "super_admin",
                                    "pedagogical_admin", "pedagogical_lead"):
        raise HTTPException(status_code=403, detail="Accès refusé")

    from app.models import ChapterPathway
    if not db.query(ChapterPathway).filter(ChapterPathway.id == score_in.chapitre_id).first():
        raise HTTPException(status_code=404, detail="Chapter pathway not found")

    with tenant_unaware():
        eleve = db.query(User).filter(User.id == score_in.eleve_id).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")

    if current_user.role == "teacher":
        from app.models import StudentEnrollment, TeacherClass
        in_class = (
            db.query(StudentEnrollment.id)
            .join(TeacherClass, TeacherClass.id == StudentEnrollment.class_id)
            .filter(
                StudentEnrollment.student_id == score_in.eleve_id,
                StudentEnrollment.is_active == True,
                TeacherClass.teacher_id == current_user.id,
            )
            .first()
        )
        if not in_class:
            raise HTTPException(
                status_code=403,
                detail="Cet élève n'est inscrit dans aucune de vos classes",
            )
    elif current_user.role in ("admin_school", "pedagogical_lead"):
        if eleve.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="Accès refusé: élève d'une autre école")

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
    current_user: User = Depends(set_tenant_context),
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
def _notion_niveau(db: Session, notion_id: int):
    """Résout Notion → Chapitre → Matière → Niveau d'étude (ou None)."""
    notion = db.query(Notion).filter(Notion.id == notion_id).first()
    if not notion:
        return None
    chapitre = db.query(ChapterPathway).filter(ChapterPathway.id == notion.chapitre_id).first()
    if not chapitre:
        return None
    matiere = db.query(Matiere).filter(Matiere.id == chapitre.matiere_id).first()
    if not matiere:
        return None
    return db.query(NiveauEtude).filter(NiveauEtude.id == matiere.niveau_etude_id).first()


def _eleve_active_niveaux(user: User, db: Session) -> set:
    """Niveaux scolaires couverts par les droits actifs de l'élève :
    PackPurchase (école + individuel) ET fallback Abonnement/PackDefinition
    (source de vérité E1). Le filtre tenant est supprimé car les
    PackPurchase individuels ont school_id=NULL."""
    from datetime import datetime, timezone
    from app.models import PackPurchase, PackPurchaseStatus, PurchaserType, StudyPack

    now = datetime.now(timezone.utc)
    niveaux: set = set()
    token = _tenant_filter_suppressed.set(True)
    try:
        if user.school_id:
            for sp in db.query(PackPurchase).filter(
                PackPurchase.school_id == user.school_id,
                PackPurchase.purchaser_type == PurchaserType.SCHOOL.value,
                PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
                PackPurchase.valid_until > now,
            ).all():
                pack = db.query(StudyPack).filter(StudyPack.id == sp.pack_id).first()
                if pack:
                    niveaux.add(pack.niveau_scolaire)

        for sp in db.query(PackPurchase).filter(
            PackPurchase.student_id == user.id,
            PackPurchase.purchaser_type == PurchaserType.STUDENT.value,
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
        ).all():
            pack = db.query(StudyPack).filter(StudyPack.id == sp.pack_id).first()
            if pack:
                niveaux.add(pack.niveau_scolaire)

        for abo in db.query(Abonnement).join(PackDefinition).filter(
            Abonnement.user_id == user.id,
            Abonnement.statut.in_(["actif", "grace"]),
            Abonnement.fin > now,
        ).all():
            if abo.pack:
                niveaux.add(abo.pack.niveau_scolaire)
    finally:
        _tenant_filter_suppressed.reset(token)
    return niveaux


@router.get("/notions/{notion_id}/contenu")
def get_contenu_a_servir(
    notion_id: int,
    eleve_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Get the content to serve for a notion, given the student's level."""
    if current_user.role == "student" and current_user.id != eleve_id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # SECURITY FIX #3 : fermeture du contournement ABAC — un élève ne peut
    # servir le contenu d'une notion que si ses packs/abonnements actifs
    # couvrent le niveau d'étude de la matière rattachée à cette notion.
    if current_user.role == "student":
        niveau = _notion_niveau(db, notion_id)
        if niveau is not None:
            covered = {_strip_accents(n or "") for n in _eleve_active_niveaux(current_user, db)}
            if _strip_accents(niveau.nom or "") not in covered:
                raise HTTPException(status_code=402, detail={
                    "message": "Cette notion nécessite un pack couvrant son niveau d'étude.",
                    "required_pack": "Basic",
                })

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


# -------------------------------------------------------------------
# Student-facing: Matieres by niveau_scolaire (langues + specialites)
# -------------------------------------------------------------------
def _strip_accents(s: str) -> str:
    """Remove accents from a string for fuzzy niveau matching."""
    import unicodedata
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii").lower().strip()


@router.get("/matieres-by-niveau")
def get_matieres_by_niveau(
    niveau_scolaire: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return matieres grouped by type_matiere for a given niveau_scolaire.

    Response: { "langues": [...], "specialites": [...] }
    Each item: { "id", "nom", "niveau_etude_id" }
    """
    with tenant_unaware():
        norm_input = _strip_accents(niveau_scolaire)
        all_niveaux = db.query(NiveauEtude).all()
        niv = None

        # 1. Exact match (accent-normalized)
        for n in all_niveaux:
            if _strip_accents(n.nom) == norm_input:
                niv = n
                break

        # 2. Prefix match on leading number (e.g. "9eme de base" -> "9" matches "9eme annee base")
        if not niv:
            import re
            m = re.match(r"(\d+)", norm_input)
            if m:
                num = m.group(1)
                for n in all_niveaux:
                    if _strip_accents(n.nom).startswith(num):
                        niv = n
                        break

        if not niv:
            return {"langues": [], "specialites": []}

        matieres = db.query(Matiere).filter(Matiere.niveau_etude_id == niv.id).all()

        langues = [
            {"id": m.id, "nom": m.nom, "niveau_etude_id": m.niveau_etude_id}
            for m in matieres if m.type_matiere == "langue"
        ]
        specialites = [
            {"id": m.id, "nom": m.nom, "niveau_etude_id": m.niveau_etude_id}
            for m in matieres if m.type_matiere == "specialite"
        ]

        return {"langues": langues, "specialites": specialites}


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
    Course, CourseStatus, CourseVisibility,
)


@router.get("/catalog")
def pathway_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
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


def _normalise(s: str) -> str:
    """Normalise une chaîne (sans accents, minuscules) pour comparer catégories/niveaux."""
    import unicodedata as _ud
    return _ud.normalize("NFD", s or "").encode("ascii", "ignore").decode("ascii").lower().strip()


def _published_courses_for_matiere(
    db: Session,
    matiere: Matiere,
    niveau_scolaire_norm: str,
    school_id: Optional[int],
) -> list[dict]:
    """Cours réellement publiés rattachés à une matière + un niveau scolaire.

    Ne conserve que les cours visibles (catalogue public OU école courante) dont :
      - Course.category correspond au nom (ou à l'ID) de la matière
      - Course.niveau_scolaire correspond au niveau de l'élève
      - Course.status == PUBLISHED ET Course.is_published == True
    """
    visible = [CourseVisibility.PUBLIC_CATALOG.value]
    if school_id is not None:
        visible.append(CourseVisibility.SCHOOL_ONLY.value)

    # Catégories candidates : nom normalisé de la matière + ID en chaîne
    matiere_nom_norm = _normalise(matiere.nom)
    cat_prefixes = {matiere_nom_norm, str(matiere.id)}

    courses = db.query(Course).filter(
        Course.status == CourseStatus.PUBLISHED.value,
        Course.is_published == True,
        Course.visibility.in_(visible),
        Course.category.isnot(None),
        Course.niveau_scolaire.isnot(None),
    ).all()

    result = []
    for c in courses:
        if not c.category:
            continue
        cat_norm = _normalise(c.category)
        if cat_norm not in cat_prefixes:
            continue
        cours_niv_norm = _normalise(c.niveau_scolaire)
        if niveau_scolaire_norm and cours_niv_norm != niveau_scolaire_norm:
            continue
        # Si school_only : seul le courant propriétaire l'a, sinon le filtre en amont
        result.append({
            "id": c.id,
            "title": c.title,
            "category": c.category,
            "niveau_scolaire": c.niveau_scolaire,
            "description": c.short_description or c.description or "",
            "thumbnail_url": c.thumbnail_url,
            "cover_url": c.cover_url,
            "is_free": (c.price_tokens or 0) == 0 and float(c.price_dt or 0) == 0,
            "total_lessons": c.total_lessons or 0,
            "total_duration_minutes": c.total_duration_minutes or 0,
        })

    # Dédupliquer par id
    seen = set()
    unique = []
    for item in result:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)
    return unique


@router.get("/mon-parcours")
def mon_parcours(
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
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

    # Fallback: System A (Abonnement + PackDefinition)
    if not active_niveaux:
        abo = db.query(Abonnement).filter(
            Abonnement.user_id == current_user.id,
            Abonnement.statut.in_(["actif", "grace"]),
        ).order_by(Abonnement.created_at.desc()).first()
        if abo and abo.pack:
            active_niveaux.add(abo.pack.niveau_scolaire)

    if not active_niveaux:
        return {"message": "Aucun pack actif. Achetez un pack pour accéder à votre parcours.", "niveaux": []}

    # Normalize: strip accents, lowercase — to match PackDefinition.niveau_scolaire vs NiveauEtude.nom
    import unicodedata as _ud
    def _norm(s):
        n = _ud.normalize("NFD", s or "")
        return "".join(c for c in n if _ud.category(c) != "Mn").lower().strip()

    norm_active = {_norm(v): v for v in active_niveaux}
    student_niveau_norm = _normalise(getattr(current_user, "niveau_scolaire", None) or "")

    with tenant_unaware():
        all_niveaux_etude = db.query(NiveauEtude).order_by(NiveauEtude.ordre).all()
        niveaux = [ne for ne in all_niveaux_etude if _norm(ne.nom) in norm_active]
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

    # Get student lesson progress (from the `progress` table, not lesson_progress)
    from sqlalchemy import text
    progress_rows = db.execute(
        text("SELECT lesson_id, status, score FROM progress WHERE user_id = :uid"),
        {"uid": current_user.id},
    ).fetchall()
    progress_map = {}
    for pr in progress_rows:
        # Find which chapter this lesson belongs to
        lesson = db.query(Lesson).filter(Lesson.id == pr.lesson_id).first()
        if lesson:
            module = db.query(Module).filter(Module.id == lesson.module_id).first()
            if module:
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

            # Ne garder la matière QUE s'il existe au moins un cours publié
            courses_data = _published_courses_for_matiere(
                db, matiere, student_niveau_norm, current_user.school_id,
            )
            if not courses_data:
                continue

            matieres_data.append({
                "id": matiere.id,
                "nom": matiere.nom,
                "chapters_count": len(chapters_data),
                "chapters": chapters_data,
                "courses": courses_data,
            })

        result.append({
            "niveau": {"id": niveau.id, "nom": niveau.nom},
            "matieres": matieres_data,
        })

    return {"niveaux": result}


@router.post("/auto-enroll-from-test")
def auto_enroll_from_test(
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Auto-enroll student in pathway based on most recent placement test result.
    No pack required — creates ProfilAssimilationEleve for all chapters of matched niveau."""
    from app.models import PlacementTest, PlacementTestResult

    # Find latest test result for this student
    latest_result = db.query(PlacementTestResult).filter(
        PlacementTestResult.user_id == current_user.id,
    ).order_by(PlacementTestResult.completed_at.desc()).first()

    if not latest_result:
        raise HTTPException(status_code=404, detail="Aucun test de positionnement complété")

    test = db.query(PlacementTest).filter(PlacementTest.id == latest_result.placement_test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test de positionnement introuvable")

    # Find matching niveau
    niveau_etude = db.query(NiveauEtude).filter(
        NiveauEtude.nom.ilike(f"%{test.niveau}%")
    ).first()
    if not niveau_etude:
        raise HTTPException(status_code=404, detail="Niveau non trouvé pour ce test")

    # Map competency_level to niveau_assimilation
    level_map = {
        "debutant": "remediation",
        "intermediaire": "standard",
        "intermédiaire": "standard",
        "avance": "avance",
    }
    niveau_assim = level_map.get(latest_result.competency_level, "standard")

    # Find matiere + chapters
    matiere = db.query(Matiere).filter(
        Matiere.niveau_etude_id == niveau_etude.id,
        Matiere.nom.ilike(f"%{test.matiere}%"),
    ).first()
    if not matiere:
        # Fallback: get all chapters for this niveau
        matieres = db.query(Matiere).filter(Matiere.niveau_etude_id == niveau_etude.id).all()
        chapters = db.query(ChapterPathway).filter(ChapterPathway.matiere_id.in_([m.id for m in matieres])).all()
    else:
        chapters = db.query(ChapterPathway).filter(ChapterPathway.matiere_id == matiere.id).all()

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
                niveau_assimilation_courant=niveau_assim,
                source_changement=SourceChangement.TEST_INITIAL.value,
                score_declencheur=latest_result.score,
                date=datetime.now(timezone.utc),
                statut_validation=StatutValidationProfil.AUTO_APPLIQUE.value,
            )
            db.add(profil)
            created += 1

    db.commit()

    return {
        "message": f"Parcours auto-inscrit. {created} chapitre(s) initialisé(s).",
        "niveau": niveau_etude.nom,
        "niveau_id": niveau_etude.id,
        "competency_level": latest_result.competency_level,
        "niveau_assimilation": niveau_assim,
        "chapters_initialized": created,
        "total_chapters": len(chapters),
    }


@router.post("/enroll-pathway")
def enroll_pathway(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
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
    """Liste les spécialités pédagogiques de l'école.

    NOTE: Uses manual `ecole_id` filter instead of the central tenant filter
    (_add_tenant_filter) because SpecialitePedagogique.ecole_id ≠ school_id.
    The central filter only matches columns named `school_id`.
    """
    specs = db.query(SpecialitePedagogique).filter(
        SpecialitePedagogique.ecole_id == current_user.school_id
    ).all() if current_user.school_id else db.query(SpecialitePedagogique).all()

    result = []
    for s in specs:
        matiere_ids = [sm.matiere_id for sm in db.query(SpecialitePedagogiqueMatiere).filter(
            SpecialitePedagogiqueMatiere.specialite_id == s.id
        ).all()]
        responsables = []
        for r in db.query(ResponsablePedagogique).filter(
            ResponsablePedagogique.specialite_id == s.id
        ).all():
            user = db.query(User).filter(User.id == r.user_id).first()
            if user:
                responsables.append({
                    "user_id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                })
        result.append({
            "id": s.id,
            "nom": s.nom,
            "cycle_scolaire": s.cycle_scolaire,
            "ecole_id": s.ecole_id,
            "matiere_ids": matiere_ids,
            "responsables": responsables,
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


@router.put("/specialites-pedagogiques/{spec_id}")
def update_specialite(
    spec_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """Met à jour une spécialité pédagogique et ses relations."""
    spec = db.query(SpecialitePedagogique).filter(SpecialitePedagogique.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Spécialité non trouvée")

    if "nom" in body:
        spec.nom = body["nom"]
    if "cycle_scolaire" in body:
        spec.cycle_scolaire = body["cycle_scolaire"]

    if "matiere_ids" in body:
        db.query(SpecialitePedagogiqueMatiere).filter(
            SpecialitePedagogiqueMatiere.specialite_id == spec_id
        ).delete()
        for matiere_id in body["matiere_ids"]:
            db.add(SpecialitePedagogiqueMatiere(specialite_id=spec_id, matiere_id=matiere_id))

    db.commit()
    db.refresh(spec)
    return {"id": spec.id, "nom": spec.nom, "message": "Spécialité mise à jour"}


@router.delete("/specialites-pedagogiques/{spec_id}")
def delete_specialite(
    spec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """Supprime une spécialité pédagogique et toutes ses relations."""
    spec = db.query(SpecialitePedagogique).filter(SpecialitePedagogique.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Spécialité non trouvée")

    db.delete(spec)
    db.commit()
    return {"message": "Spécialité supprimée"}


@router.post("/responsables-pedagogiques")
def assign_responsable(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    """Assigne un responsable pédagogique à une spécialité."""
    user_id = body.get("user_id")
    specialite_id = body.get("specialite_id")
    if not user_id or not specialite_id:
        raise HTTPException(status_code=400, detail="user_id et specialite_id requis")

    # Vérifier si l'assignation existe déjà
    existing = db.query(ResponsablePedagogique).filter(
        ResponsablePedagogique.user_id == user_id,
        ResponsablePedagogique.specialite_id == specialite_id,
    ).first()
    if existing:
        # Mettre à jour les niveaux_etude_scope si fournis
        niveaux_ids = body.get("niveaux_etude_ids", [])
        if niveaux_ids:
            from app.models import NiveauEtude
            existing.niveaux_etude_scope.clear()
            for niv_id in niveaux_ids:
                niv = db.query(NiveauEtude).filter(NiveauEtude.id == niv_id).first()
                if niv:
                    existing.niveaux_etude_scope.append(niv)
            db.commit()
            db.refresh(existing)
        return {"id": existing.id, "message": "Responsable déjà assigné, niveaux mis à jour"}

    resp = ResponsablePedagogique(
        user_id=user_id,
        specialite_id=specialite_id,
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
    current_user: User = Depends(set_tenant_context),
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
    current_user: User = Depends(set_tenant_context),
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
    current_user: User = Depends(set_tenant_context),
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
