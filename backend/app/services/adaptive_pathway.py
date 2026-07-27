"""Adaptive Pedagogical Pathway — Business logic.

Core rules:
- statut_publication: notion is publiable iff it has STANDARD + at least one other level
- niveau_effectif: resolves the current assimilation level for a student/chapter
- evaluer_reorientation: auto-reorientation based on N last scores + thresholds
- contenu_a_servir: serve content at effective level, fallback to STANDARD
- acces_effectif: dynamic access resolution through packs + profile
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal

from sqlalchemy.orm import Session

from app.models import (
    Notion, ContenuNotion, ProfilAssimilationEleve, HistoriqueScoreEleve,
    NotificationReorientation, Matiere, ChapterPathway, User,
    StudyPack, PackPurchase, PackPurchaseStatus, PurchaserType,
    NiveauAssimilation, SourceChangement, StatutValidationProfil,
    ActionReorientation,
)

logger = logging.getLogger(__name__)

# Default configuration — overridable per-matière in a future settings pass
DEFAULT_N = 5          # Number of last scores to average for reorientation
DEFAULT_DELAY_DAYS = 7  # Days for teacher to confirm/annul a reorientation

# Thresholds: moyenne -> niveau
# These are configurable per-matière; defaults here:
#   < 40  -> REMEDIATION
#   40-74 -> STANDARD
#   >= 75 -> AVANCE
DEFAULT_THRESHOLDS = {
    "remediation": 0,
    "standard": 40,
    "avance": 75,
}


# -------------------------------------------------------------------
# 1. statut_publication
# -------------------------------------------------------------------

def _existe_contenu(notion_id: int, niveau: str, db: Session) -> bool:
    """Check if at least one active content exists for a notion at a given level."""
    return db.query(ContenuNotion).filter(
        ContenuNotion.notion_id == notion_id,
        ContenuNotion.niveau_assimilation == niveau,
        ContenuNotion.statut_pedagogique == "a",
    ).first() is not None


def statut_publication(notion_id: int, db: Session) -> dict:
    """Return publication status + missing levels for a notion.

    Returns:
        {"statut": "publiable" | "brouillon", "niveaux_manquants": [...]}
    """
    a_standard = _existe_contenu(notion_id, NiveauAssimilation.STANDARD.value, db)
    a_remediation = _existe_contenu(notion_id, NiveauAssimilation.REMEDIATION.value, db)
    a_avance = _existe_contenu(notion_id, NiveauAssimilation.AVANCE.value, db)

    niveaux_manquants = []
    if not a_standard:
        niveaux_manquants.append("STANDARD")
    if not a_remediation:
        niveaux_manquants.append("REMEDIATION")
    if not a_avance:
        niveaux_manquants.append("AVANCE")

    statut = "publiable" if (a_standard and (a_remediation or a_avance)) else "brouillon"
    return {"statut": statut, "niveaux_manquants": niveaux_manquants}


# -------------------------------------------------------------------
# 2. niveau_effectif
# -------------------------------------------------------------------

def _get_profil(eleve_id: int, chapitre_id: int, db: Session) -> Optional[ProfilAssimilationEleve]:
    """Get the most recent assimilation profile for a student/chapter."""
    return db.query(ProfilAssimilationEleve).filter(
        ProfilAssimilationEleve.eleve_id == eleve_id,
        ProfilAssimilationEleve.chapitre_id == chapitre_id,
    ).order_by(ProfilAssimilationEleve.date.desc()).first()


def _get_matiere_of_chapitre(chapitre_id: int, db: Session) -> Optional[Matiere]:
    """Resolve the matiere of a chapter."""
    chapter = db.query(ChapterPathway).filter(ChapterPathway.id == chapitre_id).first()
    if chapter:
        return db.query(Matiere).filter(Matiere.id == chapter.matiere_id).first()
    return None


def _get_niveau_defaut_matiere(eleve_id: int, matiere: Optional[Matiere], db: Session) -> str:
    """Determine default assimilation level from student's niveau_scolaire.

    Tunisian levels mapping:
    - Primaire (1ère-6ème année) -> REMEDIATION
    - Préparatoire (7ème-9ème de base) -> STANDARD
    - Secondaire (1ère-4ème année) -> AVANCE
    """
    student = db.query(User).filter(User.id == eleve_id).first()
    if not student or not student.niveau_scolaire:
        return NiveauAssimilation.STANDARD.value

    niveau = student.niveau_scolaire.lower()

    # Primaire
    if any(f"{i}ere annee" in niveau or f"{i}ème année" in niveau for i in range(1, 7)):
        return NiveauAssimilation.REMEDIATION.value
    if "primaire" in niveau:
        return NiveauAssimilation.REMEDIATION.value

    # Préparatoire / collège
    if any(f"{i}eme de base" in niveau or f"{i}ème de base" in niveau for i in range(7, 10)):
        return NiveauAssimilation.STANDARD.value
    if "preparatoire" in niveau or "préparatoire" in niveau or "college" in niveau:
        return NiveauAssimilation.STANDARD.value

    # Secondaire
    if "secondaire" in niveau or any(f"{i}eme annee" in niveau or f"{i}ème année" in niveau for i in range(1, 5)):
        return NiveauAssimilation.AVANCE.value

    return NiveauAssimilation.STANDARD.value


def niveau_effectif(eleve_id: int, chapitre_id: int, db: Session) -> dict:
    """Resolve the effective assimilation level for a student on a chapter.

    Returns:
        {"eleve_id": ..., "chapitre_id": ..., "niveau_effectif": "...", "source": "profil" | "defaut_matiere"}
    """
    profil = _get_profil(eleve_id, chapitre_id, db)
    if profil:
        return {
            "eleve_id": eleve_id,
            "chapitre_id": chapitre_id,
            "niveau_effectif": profil.niveau_assimilation_courant,
            "source": "profil",
        }

    matiere = _get_matiere_of_chapitre(chapitre_id, db)
    defaut = _get_niveau_defaut_matiere(eleve_id, matiere, db)
    return {
        "eleve_id": eleve_id,
        "chapitre_id": chapitre_id,
        "niveau_effectif": defaut,
        "source": "defaut_matiere",
    }


# -------------------------------------------------------------------
# 3. evaluer_reorientation
# -------------------------------------------------------------------

def _derniers_scores(eleve_id: int, chapitre_id: int, limit: int, db: Session) -> list[float]:
    """Get the N most recent scores for a student/chapter."""
    rows = db.query(HistoriqueScoreEleve).filter(
        HistoriqueScoreEleve.eleve_id == eleve_id,
        HistoriqueScoreEleve.chapitre_id == chapitre_id,
    ).order_by(HistoriqueScoreEleve.date.desc()).limit(limit).all()
    return [r.score for r in rows]


def _resoudre_niveau(moyenne: float, seuils: dict) -> str:
    """Map a moyenne to an assimilation level using thresholds."""
    if moyenne >= seuils.get("avance", 75):
        return NiveauAssimilation.AVANCE.value
    elif moyenne >= seuils.get("standard", 40):
        return NiveauAssimilation.STANDARD.value
    else:
        return NiveauAssimilation.REMEDIATION.value


def _notifier_enseignant(
    profil: ProfilAssimilationEleve,
    enseignant_id: int,
    delay_days: int,
    db: Session,
) -> NotificationReorientation:
    """Create a notification for the teacher about a reorientation."""
    now = datetime.now(timezone.utc)
    notification = NotificationReorientation(
        profil_assimilation_id=profil.id,
        enseignant_id=enseignant_id,
        date_notification=now,
        date_limite_action=now + timedelta(days=delay_days),
        action_prise=ActionReorientation.AUCUNE.value,
    )
    db.add(notification)
    db.flush()
    return notification


def evaluer_reorientation(
    eleve_id: int,
    chapitre_id: int,
    db: Session,
    enseignant_id: Optional[int] = None,
    config_n: Optional[int] = None,
    config_seuils: Optional[dict] = None,
    config_delay_days: Optional[int] = None,
) -> Optional[dict]:
    """Evaluate whether a student should be reoriented based on recent scores.

    Returns the new profile dict if reorientation occurred, None otherwise.
    """
    n = config_n or DEFAULT_N
    seuils = config_seuils or DEFAULT_THRESHOLDS
    delay_days = config_delay_days or DEFAULT_DELAY_DAYS

    scores = _derniers_scores(eleve_id, chapitre_id, n, db)
    if len(scores) < 1:
        return None

    moyenne = sum(scores) / len(scores)
    nouveau_niveau = _resoudre_niveau(moyenne, seuils)
    niveau_actuel_info = niveau_effectif(eleve_id, chapitre_id, db)
    niveau_actuel = niveau_actuel_info["niveau_effectif"]

    if nouveau_niveau == niveau_actuel:
        return None

    # Create new profile record
    profil = ProfilAssimilationEleve(
        eleve_id=eleve_id,
        chapitre_id=chapitre_id,
        niveau_assimilation_courant=nouveau_niveau,
        source_changement=SourceChangement.AJUSTEMENT_AUTO.value,
        score_declencheur=moyenne,
        date=datetime.now(timezone.utc),
        statut_validation=StatutValidationProfil.AUTO_APPLIQUE.value,
    )
    db.add(profil)
    db.flush()

    # Notify teacher if provided
    if enseignant_id:
        _notifier_enseignant(profil, enseignant_id, delay_days, db)

    db.commit()

    return {
        "profil_id": profil.id,
        "eleve_id": eleve_id,
        "chapitre_id": chapitre_id,
        "ancien_niveau": niveau_actuel,
        "nouveau_niveau": nouveau_niveau,
        "moyenne": moyenne,
        "statut_validation": profil.statut_validation,
        "notification_envoyee": enseignant_id is not None,
    }


# -------------------------------------------------------------------
# 4. contenu_a_servir
# -------------------------------------------------------------------

def contenu_a_servir(notion_id: int, eleve_id: int, db: Session) -> Optional[dict]:
    """Resolve which content to serve for a notion, given the student's level.

    Fallback: if no content at effective level, serve STANDARD.
    If no STANDARD either, serve any available content.
    Returns None only if the notion has absolutely no content.
    """
    # Resolve effective level from the notion's parent chapter
    notion = db.query(Notion).filter(Notion.id == notion_id).first()
    if not notion:
        return None

    niveau_info = niveau_effectif(eleve_id, notion.chapitre_id, db)
    niveau = niveau_info["niveau_effectif"]

    # Try effective level
    contenu = db.query(ContenuNotion).filter(
        ContenuNotion.notion_id == notion_id,
        ContenuNotion.niveau_assimilation == niveau,
        ContenuNotion.statut_pedagogique == "a",
    ).first()
    if contenu:
        return {
            "contenu_id": contenu.id,
            "niveau_servi": niveau,
            "type_ressource": contenu.type_ressource,
            "contenu": contenu.contenu,
            "fallback": False,
        }

    # Fallback to STANDARD
    contenu = db.query(ContenuNotion).filter(
        ContenuNotion.notion_id == notion_id,
        ContenuNotion.niveau_assimilation == NiveauAssimilation.STANDARD.value,
        ContenuNotion.statut_pedagogique == "a",
    ).first()
    if contenu:
        return {
            "contenu_id": contenu.id,
            "niveau_servi": NiveauAssimilation.STANDARD.value,
            "type_ressource": contenu.type_ressource,
            "contenu": contenu.contenu,
            "fallback": True,
        }

    # Last resort: any active content
    contenu = db.query(ContenuNotion).filter(
        ContenuNotion.notion_id == notion_id,
        ContenuNotion.statut_pedagogique == "a",
    ).first()
    if contenu:
        return {
            "contenu_id": contenu.id,
            "niveau_servi": contenu.niveau_assimilation,
            "type_ressource": contenu.type_ressource,
            "contenu": contenu.contenu,
            "fallback": True,
        }

    return None


# -------------------------------------------------------------------
# 5. acces_effectif
# -------------------------------------------------------------------

def _get_pack_actif(eleve_id: int, db: Session) -> Optional[StudyPack]:
    """Get the active pack (school or student) for a student.

    Priority: school pack (via school_id) > student pack (via student_id).
    """
    now = datetime.now(timezone.utc)
    student = db.query(User).filter(User.id == eleve_id).first()
    if not student:
        return None

    # Priority 1: school pack
    if student.school_id:
        purchase = db.query(PackPurchase).join(StudyPack).filter(
            PackPurchase.school_id == student.school_id,
            PackPurchase.purchaser_type == PurchaserType.SCHOOL.value,
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
        ).first()
        if purchase:
            return purchase.pack

    # Priority 2: individual student pack
    purchase = db.query(PackPurchase).join(StudyPack).filter(
        PackPurchase.student_id == eleve_id,
        PackPurchase.purchaser_type == PurchaserType.STUDENT.value,
        PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
        PackPurchase.valid_until > now,
    ).first()
    if purchase:
        return purchase.pack
    return None


def acces_effectif(
    eleve_id: int,
    matiere_id: int,
    chapitre_id: int,
    db: Session,
) -> dict:
    """Resolve effective access for a student on a specific chapter.

    Returns:
        {"eleve_id": ..., "matiere_id": ..., "chapitre_id": ...,
         "acces": bool, "niveau_effectif": str | None}
    """
    pack = _get_pack_actif(eleve_id, db)
    if not pack:
        return {
            "eleve_id": eleve_id,
            "matiere_id": matiere_id,
            "chapitre_id": chapitre_id,
            "acces": False,
            "niveau_effectif": None,
        }

    # Check if pack covers the matiere
    if pack.matieres:
        matieres_list = pack.matieres if isinstance(pack.matieres, list) else []
        # Get matiere name
        matiere = db.query(Matiere).filter(Matiere.id == matiere_id).first()
        if matiere and matiere.nom not in matieres_list:
            return {
                "eleve_id": eleve_id,
                "matiere_id": matiere_id,
                "chapitre_id": chapitre_id,
                "acces": False,
                "niveau_effectif": None,
            }

    # Access granted — resolve dynamic level (NEVER from scope_achat)
    niveau_info = niveau_effectif(eleve_id, chapitre_id, db)
    return {
        "eleve_id": eleve_id,
        "matiere_id": matiere_id,
        "chapitre_id": chapitre_id,
        "acces": True,
        "niveau_effectif": niveau_info["niveau_effectif"],
    }
