"""
Service de calcul du palier élève (tier) — source de vérité unique.
Ne stocke JAMAIS le résultat : calcul dynamique à chaque appel basé sur l'Abonnement actif.

SOURCE DE VÉRITÉ (depuis la correction E1) : la table `abonnements`
(Abonnement + PackDefinition) — le système legacy PackPurchase/StudyPack
n'est PLUS lu pour déterminer le palier.

Paliers bruts (pack tier, renvoyés au frontend) :
  - "gratuit"            : pas d'abonnement actif ou pack gratuit (état par défaut)
  - "basique"/"basic"    : pack Basique
  - "silver"             : pack Silver
  - "golden"             : pack Golden

Paliers legacy (compatibilité interne recommandations/gamification/objectifs/IA) :
  - "decouverte"     ← gratuit / sans abonnement
  - "excellence"     ← basique/basic
  - "etablissement"  ← silver/golden
"""
import logging
from datetime import datetime, timezone
from typing import Literal, Optional

from sqlalchemy.orm import Session

from app.models import User

logger = logging.getLogger(__name__)

# Palier brut exposé au frontend (= tier du pack de l'Abonnement actif)
StudentPackTier = str

# Paliers legacy dérivés (compatibilité des consommateurs internes)
StudentTier = Literal["decouverte", "excellence", "etablissement"]
AIFeatureLevel = Literal["basic", "adaptive", "curriculum_aligned"]

FREE_TIERS = {"gratuit", "free", ""}
BASIC_TIERS = {"basique", "basic"}
SILVER_TIERS = {"silver"}
GOLDEN_TIERS = {"golden"}

PAID_PACK_TIERS = BASIC_TIERS | SILVER_TIERS | GOLDEN_TIERS


def get_active_abonnement(user: User, db: Session):
    """Abonnement actif (statut actif/grace et fin future) le plus récent, ou None."""
    from app.models import Abonnement
    from datetime import datetime as dt, timezone as tz
    now = dt.now(tz.utc)
    return db.query(Abonnement).filter(
        Abonnement.user_id == user.id,
        Abonnement.statut.in_(["actif", "grace"]),
        Abonnement.fin > now,
    ).order_by(Abonnement.created_at.desc()).first()


def get_student_pack_tier(user: User, db: Session) -> StudentPackTier:
    """
    SOURCE DE VÉRITÉ UNIQUE du palier élève : l'Abonnement actif.
    Retourne le tier brut du pack (lowercase), ou "gratuit" si aucun
    abonnement actif / pack gratuit. Ne lit JAMAIS PackPurchase.
    """
    abo = get_active_abonnement(user, db)
    if not abo or not abo.pack:
        return "gratuit"
    return (abo.pack.tier or "").strip().lower() or "gratuit"


def _legacy_tier(pack_tier: Optional[str]) -> StudentTier:
    """Mappe le tier du pack (Abonnement) vers les paliers legacy internes."""
    t = (pack_tier or "").strip().lower()
    if t in GOLDEN_TIERS or t in SILVER_TIERS:
        return "etablissement"
    if t in BASIC_TIERS:
        return "excellence"
    return "decouverte"


def get_student_tier(user: User, db: Session) -> StudentTier:
    """
    Détermine le palier de l'élève en temps réel à partir de son Abonnement actif.
    (Correction E1 : ne lit plus PackPurchase/StudyPack.)
    Ordre de priorité : golden/silver > basique > decouverte.
    """
    return _legacy_tier(get_student_pack_tier(user, db))


def is_paid_pack_tier(pack_tier: Optional[str]) -> bool:
    """True si le tier du pack correspond à un pack payant."""
    return (pack_tier or "").strip().lower() in PAID_PACK_TIERS


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


def ensure_free_abonnement(user: User, db: Session):
    """Garantit le contrat Freemium : tout élève a TOUJOURS un Abonnement
    "gratuit" actif couvrant son niveau_scolaire courant.

    Appelée :
      - à l'inscription (auth.register) ;
      - après un changement de niveau_scolaire qui a invalidé les
        abonnements incompatibles (users.update_current_user_profile).

    Ne crée RIEN si l'élève a déjà un abonnement actif/grace ou si aucun
    PackDefinition "gratuit" actif n'existe pour son niveau.
    Fait flush() (id disponible) mais laisse le COMMIT à l'appelant.
    Retourne l'Abonnement créé, ou None.
    """
    from datetime import timedelta
    from app.models import Abonnement, PackDefinition

    if not getattr(user, "niveau_scolaire", None):
        return None

    has_active = db.query(Abonnement).filter(
        Abonnement.user_id == user.id,
        Abonnement.statut.in_(["actif", "grace"]),
    ).first()
    if has_active:
        return None

    free_pack = db.query(PackDefinition).filter(
        PackDefinition.tier == "gratuit",
        PackDefinition.est_actif == True,  # noqa: E712
        PackDefinition.niveau_scolaire == user.niveau_scolaire,
    ).first()
    if not free_pack:
        logger.warning(
            "ensure_free_abonnement: aucun pack gratuit actif pour le niveau %r "
            "(user %s) — contrat Freemium non garanti", user.niveau_scolaire, user.id,
        )
        return None

    now = datetime.now(timezone.utc)
    abo = Abonnement(
        user_id=user.id,
        pack_id=free_pack.id,
        statut="actif",
        debut=now,
        fin=now + timedelta(days=365),
    )
    db.add(abo)
    db.flush()
    return abo
