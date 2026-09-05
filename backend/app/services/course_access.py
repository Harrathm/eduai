"""
Service centralisé de vérification d'accès aux cours.
Vérifie l'accès via : gratuité, inscription, pack individuel, pack école, ABAC (tag_pack_requis).
Aucune inscription individuelle n'est créée pour un pack — l'accès est recalculé dynamiquement.
"""
import logging
import unicodedata as _ud
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    User, Course, CourseStatus, CourseEnrollment, StudyPack, PackPurchase,
    PackPurchaseStatus, SchoolCourseAccess, CoursePurchase,
    Abonnement, PackDefinition,
)
from sqlalchemy import or_, and_
from app.db.session import _tenant_filter_suppressed

logger = logging.getLogger(__name__)


def _normalize_niveau(s: str) -> str:
    """Strip accents, lowercase, collapse spaces — used for niveau_scolaire comparisons."""
    n = _ud.normalize("NFD", s or "")
    return " ".join(c for c in n if _ud.category(c) != "Mn").lower().strip()


def _matieres_config_to_names(db: Session, matieres_config) -> set:
    """
    Résout un matieres_config d'abonnement en noms de matières NORMALISÉS
    (sans accents, minuscules), comparables à Course.category normalisé.

    Accepte :
      - des IDs numériques de la table Matiere  → {"matieres": [1, 2]}
      - des IDs sous forme de chaîne            → {"matieres": ["1"]}
      - des noms bruts (ancien format)          → {"matieres": ["Mathématiques"]}

    Retourne un set vide si aucune matière n'est configurée.
    """
    if isinstance(matieres_config, dict):
        raw = matieres_config.get("matieres", [])
    elif isinstance(matieres_config, list):
        raw = matieres_config
    else:
        return set()

    names = []
    numeric_ids = []
    for entry in raw or []:
        if isinstance(entry, bool):
            continue
        if isinstance(entry, int):
            numeric_ids.append(entry)
        elif isinstance(entry, str):
            if entry.strip().isdigit():
                numeric_ids.append(int(entry.strip()))
            elif entry.strip():
                names.append(entry)

    if numeric_ids:
        from app.models import Matiere
        rows = db.query(Matiere).filter(Matiere.id.in_(numeric_ids)).all()
        names.extend(m.nom for m in rows)

    return {_normalize_niveau(n) for n in names}

# ABAC tier hierarchy: higher tier grants access to lower tier requirements
TIER_HIERARCHY = {
    "Basic": 1,
    "Silver": 2,
    "Golden": 3,
}

# Alias de normalisation : forme canonique <- alias insensible à la casse
_TIER_CANONICAL = {
    "basic": "Basic",
    "basique": "Basic",
    "silver": "Silver",
    "golden": "Golden",
}


def _tier_level(tier: str) -> int:
    """Niveau hiérarchique d'un tier, insensible à la casse (Basic/Silver/Golden)."""
    canonical = _TIER_CANONICAL.get((tier or "").lower())
    return TIER_HIERARCHY.get(canonical, 0)


def _required_tier_level(tag: str) -> int:
    """Niveau requis pour un tag_pack_requis, insensible à la casse (défaut Basic)."""
    return _tier_level(tag) or 1


def has_course_access(user: User, course: Course, db: Session) -> bool:
    """
    Vérifie si un utilisateur a accès à un cours.
    Ordre de vérification :
      0. Cours Soft_Skill → accès si pack Golden OU cours acheté
      0b. Cours Teacher_Training → accès par inscription directe ou Bulk Seats (pas d'ABAC)
      1. Cours gratuit (price=None ou 0) ou déjà acheté individuellement
      2. L'utilisateur est l'auteur du cours
      3. Inscription existante (CourseEnrollment)
      4. Achat individuel du cours (CoursePurchase)
      5. Accès école via SchoolCourseAccess
      6. Pack individuel actif (student) — niveau + matières correspondent
      7. Pack école actif (school) — niveau de l'ÉLÈVE + matières correspondent
      8. ABAC: vérifie le tag_pack_requis via le système d'abonnement
    """
    category_cible = getattr(course, "category_cible", "Scolaire") or "Scolaire"

    # 0a. Cours Soft_Skill : accès si pack Golden OU cours acheté individuellement
    if category_cible == "Soft_Skill":
        purchase = db.query(CoursePurchase).filter(
            CoursePurchase.student_id == user.id,
            CoursePurchase.course_id == course.id,
        ).first()
        if purchase:
            return True
        # Vérifie si l'utilisateur a un abonnement Golden
        now = datetime.now(timezone.utc)
        token = _tenant_filter_suppressed.set(True)
        try:
            abonnement = db.query(Abonnement).join(PackDefinition).filter(
                Abonnement.user_id == user.id,
                Abonnement.statut.in_(["actif", "grace"]),
                Abonnement.fin > now,
            ).order_by(Abonnement.created_at.desc()).first()
        finally:
            _tenant_filter_suppressed.reset(token)
        if abonnement and abonnement.pack:
            pack_tier = abonnement.pack.tier or ""
            if pack_tier.lower() == "golden":
                return True
        return False

    # 0b. Cours Teacher_Training : pas d'ABAC — accès par inscription directe ou Bulk Seats
    if category_cible == "Teacher_Training":
        enrollment = db.query(CourseEnrollment).filter(
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.course_id == course.id,
        ).first()
        if enrollment and enrollment.status == "active":
            return True
        purchase = db.query(CoursePurchase).filter(
            CoursePurchase.student_id == user.id,
            CoursePurchase.course_id == course.id,
        ).first()
        if purchase:
            return True
        if user.school_id:
            sca = db.query(SchoolCourseAccess).filter(
                SchoolCourseAccess.school_id == user.school_id,
                SchoolCourseAccess.course_id == course.id,
                SchoolCourseAccess.is_active == True,
            ).first()
            if sca:
                return True
        return False

    # 1. Cours gratuit
    if course.price is None or course.price == 0:
        return True

    # 2. Auteur du cours
    if course.author_id == user.id:
        return True

    # 3. Inscription existante
    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id,
        CourseEnrollment.course_id == course.id,
    ).first()
    if enrollment and enrollment.status == "active":
        return True

    # 4. Achat individuel du cours (CoursePurchase)
    purchase = db.query(CoursePurchase).filter(
        CoursePurchase.student_id == user.id,
        CoursePurchase.course_id == course.id,
    ).first()
    if purchase:
        return True

    # 5. Accès école via SchoolCourseAccess
    if user.school_id:
        sca = db.query(SchoolCourseAccess).filter(
            SchoolCourseAccess.school_id == user.school_id,
            SchoolCourseAccess.course_id == course.id,
            SchoolCourseAccess.is_active == True,
        ).first()
        if sca:
            return True

    # 6. Pack individuel actif (student)
    #    Suppress tenant filter — student-level PackPurchase has school_id=None
    #    which would be excluded by the automatic school_id filter.
    now = datetime.now(timezone.utc)
    token = _tenant_filter_suppressed.set(True)
    try:
        individual_packs = db.query(PackPurchase).join(StudyPack).filter(
            PackPurchase.student_id == user.id,
            PackPurchase.purchaser_type == "student",
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
            StudyPack.status == "published",
        ).all()
    finally:
        _tenant_filter_suppressed.reset(token)

    for pp in individual_packs:
        # Le pack doit couvrir le niveau de l'ÉLÈVE (pas seulement celui du cours)
        if _normalize_niveau(getattr(pp.pack, "niveau_scolaire", None)) != _normalize_niveau(user.niveau_scolaire):
            continue
        if _pack_covers_course(pp.pack, course):
            return True

    # 7. Pack école actif (school) — vérifie le niveau de l'ÉLÈVE
    #    Suppress tenant filter — explicit school_id filter already scopes correctly.
    if user.school_id and user.niveau_scolaire:
        token = _tenant_filter_suppressed.set(True)
        try:
            school_packs = db.query(PackPurchase).join(StudyPack).filter(
                PackPurchase.school_id == user.school_id,
                PackPurchase.purchaser_type == "school",
                PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
                PackPurchase.valid_until > now,
                StudyPack.status == "published",
            ).all()
        finally:
            _tenant_filter_suppressed.reset(token)

        for sp in school_packs:
            # Le pack doit couvrir le niveau de l'ÉLÈVE (pas seulement celui du cours)
            if _normalize_niveau(getattr(sp.pack, "niveau_scolaire", None)) != _normalize_niveau(user.niveau_scolaire):
                continue
            if _pack_covers_course(sp.pack, course):
                return True

    # 8. ABAC: vérifie le tag_pack_requis via le système d'abonnement
    if check_abac_access(user, course, db):
        return True

    return False


def _pack_covers_course(pack: StudyPack, course: Course) -> bool:
    """
    Vérifie si un pack couvre un cours donné.
    Le niveau du cours doit correspondre au niveau du pack (accent-insensitive).
    Si pack.matieres est null → toutes les matières sont couvertes.
    Sinon → la matière du cours doit être dans la liste du pack.
    """
    if _normalize_niveau(course.niveau_scolaire) != _normalize_niveau(pack.niveau_scolaire):
        return False
    if pack.matieres is None:
        return True
    if not isinstance(pack.matieres, list):
        return True
    return course.category in pack.matieres


def check_abac_access(user: User, course: Course, db: Session) -> bool:
    """
    Vérifie l'accès ABAC basé sur tag_pack_requis du cours et l'abonnement de l'utilisateur.

    Règles :
      - tag_pack_requis="Basic" → abonnement Basic, Silver ou Golden requis
      - tag_pack_requis="Silver" → abonnement Silver ou Golden requis
      - tag_pack_requis="Golden" → abonnement Golden requis
      - Règle des matières : Basic/Silver → vérifie que course.category est dans matieres_config
      - Pour les cours Soft_Skill : accès Golden requis (pas de vérification matière)
      - Pour les cours Teacher_Training : ABAC non applicable (pass-through)

    Retourne True si l'accès est accordé, False sinon.
    Lève HTTPException 402 si accès refusé pour upsell.
    """
    category_cible = getattr(course, "category_cible", "Scolaire") or "Scolaire"

    # Teacher_Training : ABAC non applicable
    if category_cible == "Teacher_Training":
        return True

    tag_requis = getattr(course, "tag_pack_requis", "Basic") or "Basic"
    required_level = _required_tier_level(tag_requis)

    # Recherche l'abonnement actif de l'utilisateur (statut actif ou grace)
    now = datetime.now(timezone.utc)
    token = _tenant_filter_suppressed.set(True)
    try:
        abonnement = db.query(Abonnement).join(PackDefinition).filter(
            Abonnement.user_id == user.id,
            Abonnement.statut.in_(["actif", "grace"]),
            Abonnement.fin > now,
        ).order_by(Abonnement.created_at.desc()).first()
    finally:
        _tenant_filter_suppressed.reset(token)

    if not abonnement:
        return False

    # Vérifie le tier du pack
    pack_tier = abonnement.pack.tier if abonnement.pack else "Basic"
    user_tier_level = _tier_level(pack_tier)

    if user_tier_level < required_level:
        return False

    # Règle des matières : Basic et Silver vérifient la matière (Scolaire uniquement).
    # Golden → bypass : accès illimité, aucune vérification de matière.
    if pack_tier.lower() in ("basic", "basique", "silver") and category_cible == "Scolaire":
        allowed_names = _matieres_config_to_names(
            db, abonnement.pack.matieres if abonnement.pack else None
        )
        # Si des matières sont configurées, la catégorie du cours doit y correspondre
        # (comparaison normalisée : insensible aux accents et à la casse).
        if allowed_names and course.category:
            if _normalize_niveau(course.category) not in allowed_names:
                return False

    return True


def require_abac_access(user: User, course: Course, db: Session) -> None:
    """
    Variante de check_abac_access qui lève une HTTPException 402 si l'accès est refusé.
    Utile pour les endpoints qui doivent bloquer avec un message d'upsell.
    """
    category_cible = getattr(course, "category_cible", "Scolaire") or "Scolaire"

    # Teacher_Training : ABAC non applicable
    if category_cible == "Teacher_Training":
        return

    tag_requis = getattr(course, "tag_pack_requis", "Basic") or "Basic"
    required_level = _required_tier_level(tag_requis)

    now = datetime.now(timezone.utc)
    token = _tenant_filter_suppressed.set(True)
    try:
        abonnement = db.query(Abonnement).join(PackDefinition).filter(
            Abonnement.user_id == user.id,
            Abonnement.statut.in_(["actif", "grace"]),
            Abonnement.fin > now,
        ).order_by(Abonnement.created_at.desc()).first()
    finally:
        _tenant_filter_suppressed.reset(token)

    if not abonnement:
        raise HTTPException(
            status_code=402,
            detail={
                "message": f"Accès requis : ce cours nécessite un abonnement {tag_requis}. "
                           f"Veuillez souscrire à un pack pour accéder à ce contenu.",
                "required_pack": tag_requis,
            },
        )

    pack_tier = abonnement.pack.tier if abonnement.pack else "Basic"
    user_tier_level = _tier_level(pack_tier)

    if user_tier_level < required_level:
        raise HTTPException(
            status_code=402,
            detail={
                "message": f"Upgrade requis : ce cours nécessite un pack {tag_requis}. "
                           f"Votre pack actuel ({pack_tier}) ne couvre pas ce niveau.",
                "required_pack": tag_requis,
            },
        )

    # Règle des matières (Scolaire uniquement).
    # Golden → bypass : accès illimité, aucune vérification de matière.
    if pack_tier.lower() in ("basic", "basique", "silver") and category_cible == "Scolaire":
        allowed_names = _matieres_config_to_names(
            db, abonnement.pack.matieres if abonnement.pack else None
        )
        if allowed_names and course.category:
            if _normalize_niveau(course.category) not in allowed_names:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "message": f"Matière non incluse : '{course.category}' n'est pas dans votre pack {pack_tier}. "
                                   f"Matières disponibles : {', '.join(sorted(allowed_names))}",
                        "required_pack": "Golden",
                    },
                )
    return True


def get_accessible_course_ids(user: User, db: Session) -> set:
    """
    Retourne l'ensemble des IDs de cours auxquels l'utilisateur a accès.
    Utilisé pour filtrer les listings (catalog, learner).
    
    Règles :
    - Cours gratuits → toujours accessible
    - Cours avec enrollment actif → accessible
    - Cours achetés individuellement (CoursePurchase) → accessible
    - SchoolCourseAccess → accessible
    - Pack individuel (StudyPack/PackPurchase) → accessible si niveau+matières matchent
    - Pack école (StudyPack/PackPurchase) → accessible si niveau+matières matchent
    - Cours Soft_Skill → accessible si pack Golden OU achat individuel
    - Cours Scolaire → accessible si tag_pack_requis couvert par le tier de l'abonnement
      + matière dans la config du pack (pour Basic/Silver)
    """
    now = datetime.now(timezone.utc)
    accessible = set()

    # Tous les cours publiés — aligné sur Course.status (pas le booléen is_published)
    all_courses = db.query(Course).filter(Course.status == CourseStatus.PUBLISHED).all()
    course_map = {c.id: c for c in all_courses}

    # 1. Cours gratuits
    for c in all_courses:
        if (c.price is None or c.price == 0) and (c.category_cible or "Scolaire") != "Teacher_Training":
            accessible.add(c.id)

    # 2. Enrollments actifs
    enrollments = db.query(CourseEnrollment.course_id).filter(
        CourseEnrollment.student_id == user.id,
        CourseEnrollment.status == "active",
    ).all()
    for (cid,) in enrollments:
        accessible.add(cid)

    # 3. Achats individuels
    purchases = db.query(CoursePurchase.course_id).filter(
        CoursePurchase.student_id == user.id,
    ).all()
    for (cid,) in purchases:
        accessible.add(cid)

    # 4. SchoolCourseAccess
    if user.school_id:
        scas = db.query(SchoolCourseAccess.course_id).filter(
            SchoolCourseAccess.school_id == user.school_id,
            SchoolCourseAccess.is_active == True,
        ).all()
        for (cid,) in scas:
            accessible.add(cid)

    # 5-6. Packs StudyPack/PackPurchase (deprecated mais encore actif)
    token = _tenant_filter_suppressed.set(True)
    try:
        # Pack individuel
        individual_packs = db.query(PackPurchase).join(StudyPack).filter(
            PackPurchase.student_id == user.id,
            PackPurchase.purchaser_type == "student",
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
            StudyPack.status == "published",
        ).all()
        for pp in individual_packs:
            if pp.pack:
                for c in all_courses:
                    if c.id not in accessible and _pack_covers_course(pp.pack, c):
                        accessible.add(c.id)

        # Pack école
        if user.school_id:
            school_packs = db.query(PackPurchase).join(StudyPack).filter(
                PackPurchase.school_id == user.school_id,
                PackPurchase.purchaser_type == "school",
                PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
                PackPurchase.valid_until > now,
                StudyPack.status == "published",
            ).all()
            for pp in school_packs:
                if pp.pack:
                    for c in all_courses:
                        if c.id not in accessible and _pack_covers_course(pp.pack, c):
                            accessible.add(c.id)
    finally:
        _tenant_filter_suppressed.reset(token)

    # 7. Soft_Skill : accès si pack Golden OU déjà acheté (déjà couvert par purchases ci-dessus)
    #    Ajoute golden abonnement pour les soft skills
    token = _tenant_filter_suppressed.set(True)
    try:
        abonnement = db.query(Abonnement).join(PackDefinition).filter(
            Abonnement.user_id == user.id,
            Abonnement.statut.in_(["actif", "grace"]),
            Abonnement.fin > now,
        ).order_by(Abonnement.created_at.desc()).first()
    finally:
        _tenant_filter_suppressed.reset(token)

    if abonnement and abonnement.pack:
        pack_tier = abonnement.pack.tier or ""
        user_tier_level = _tier_level(pack_tier)
        allowed_names = _matieres_config_to_names(
            db, abonnement.pack.matieres if abonnement.pack else None
        )

        for c in all_courses:
            if c.id in accessible:
                continue
            cat = getattr(c, "category_cible", "Scolaire") or "Scolaire"

            # Soft_Skill : golden donne accès
            if cat == "Soft_Skill" and pack_tier.lower() == "golden":
                accessible.add(c.id)
                continue

            # Scolaire : vérifie tag_pack_requis + matière
            if cat == "Scolaire":
                tag = getattr(c, "tag_pack_requis", "Basic") or "Basic"
                req_level = _required_tier_level(tag)
                if user_tier_level < req_level:
                    continue
                # Basic/Silver : la catégorie du cours doit faire partie des
                # matières autorisées (comparaison normalisée IDs→noms).
                if (
                    pack_tier.lower() in ("basic", "basique", "silver")
                    and allowed_names
                    and c.category
                    and _normalize_niveau(c.category) not in allowed_names
                ):
                    continue
                accessible.add(c.id)

    return accessible


def expire_pack_purchases(db_session=None):
    """
    Passe automatiquement le status des PackPurchase à 'expired'
    quand valid_until est dépassé. Ne supprime jamais les lignes.
    Si db_session est fourni, l'utilise ; sinon crée une session propre.
    """
    own_session = db_session is None
    if own_session:
        from app.db import SessionLocal
        db = SessionLocal()
    else:
        db = db_session
    try:
        now = datetime.now(timezone.utc)
        expired = db.query(PackPurchase).filter(
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until < now,
        ).all()

        count = 0
        for purchase in expired:
            purchase.status = PackPurchaseStatus.EXPIRED.value
            count += 1
            logger.info(
                f"Pack expiré: pack_purchase_id={purchase.id}, "
                f"pack_id={purchase.pack_id}, "
                f"purchaser_type={purchase.purchaser_type}"
            )

        if count > 0:
            db.commit()
            logger.info(f"{count} achat(s) de pack(s) expiré(s)")

        return count
    except Exception as e:
        if own_session:
            db.rollback()
        logger.error(f"Erreur expiration packs: {e}")
        raise
    finally:
        if own_session:
            db.close()


def start_pack_expiration_scheduler():
    """Démarre le planificateur d'expiration des packs."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            expire_pack_purchases,
            trigger=IntervalTrigger(hours=1),
            id="pack_expiration_check",
            name="Vérification des packs expirés",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Planificateur d'expiration des packs démarré")
        return scheduler
    except ImportError:
        logger.warning("APScheduler non installé. Expiration des packs non automatique.")
        return None
