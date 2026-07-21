"""
Service de calcul du palier élève (tier) — source de vérité unique.
Ne stocke JAMAIS le résultat : calcul dynamique à chaque appel basé sur PackPurchase réel.

Paliers :
  - "etablissement" : PackPurchase actif purchaser_type="school" pour le niveau de l'élève
  - "excellence"    : PackPurchase actif purchaser_type="student"
  - "decouverte"    : pas de PackPurchase actif (état par défaut)
"""
import logging
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from app.models import User, StudyPack, PackPurchase, PackPurchaseStatus

logger = logging.getLogger(__name__)

StudentTier = Literal["decouverte", "excellence", "etablissement"]
AIFeatureLevel = Literal["basic", "adaptive", "curriculum_aligned"]


def get_student_tier(user: User, db: Session) -> StudentTier:
    """
    Détermine le palier de l'élève en temps réel à partir de ses PackPurchase actifs.
    Ordre de priorité : établissement > excellence > decouverte.
    """
    now = datetime.now(timezone.utc)

    # 1. Pack Établissement (école) actif pour le niveau de l'élève
    if user.school_id and user.niveau_scolaire:
        school_pack = db.query(PackPurchase).join(StudyPack).filter(
            PackPurchase.school_id == user.school_id,
            PackPurchase.purchaser_type == "school",
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
            StudyPack.niveau_scolaire == user.niveau_scolaire,
            StudyPack.status == "published",
        ).first()
        if school_pack:
            return "etablissement"

    # 2. Pack Excellence (individuel) actif
    if user.niveau_scolaire:
        student_pack = db.query(PackPurchase).join(StudyPack).filter(
            PackPurchase.student_id == user.id,
            PackPurchase.purchaser_type == "student",
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
            StudyPack.niveau_scolaire == user.niveau_scolaire,
            StudyPack.status == "published",
        ).first()
        if student_pack:
            return "excellence"

    # 3. Pas de pack actif → Découverte (par défaut)
    return "decouverte"


def get_ai_feature_level(user: User, db: Session) -> AIFeatureLevel:
    """
    Détermine le niveau de fonctionnalité IA autorisé selon le palier élève.
    Indépendant du wallet de crédits (quantité) — gère la PROFONDEUR uniquement.
    """
    tier = get_student_tier(user, db)
    return {
        "decouverte": "basic",
        "excellence": "adaptive",
        "etablissement": "curriculum_aligned",
    }[tier]
