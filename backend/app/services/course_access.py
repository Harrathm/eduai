"""
Service centralisé de vérification d'accès aux cours.
Vérifie l'accès via : gratuité, inscription, pack individuel, pack école, ABAC (tag_pack_requis).
Aucune inscription individuelle n'est créée pour un pack — l'accès est recalculé dynamiquement.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    User, Course, CourseEnrollment, StudyPack, PackPurchase,
    PackPurchaseStatus, SchoolCourseAccess, CoursePurchase,
    Abonnement, PackDefinition,
)
from app.db.session import _tenant_filter_suppressed

logger = logging.getLogger(__name__)

# ABAC tier hierarchy: higher tier grants access to lower tier requirements
TIER_HIERARCHY = {
    "Basic": 1,
    "Silver": 2,
    "Golden": 3,
}


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
        individual_pack = db.query(PackPurchase).join(StudyPack).filter(
            PackPurchase.student_id == user.id,
            PackPurchase.purchaser_type == "student",
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
            StudyPack.niveau_scolaire == user.niveau_scolaire,
            StudyPack.status == "published",
        ).first()
    finally:
        _tenant_filter_suppressed.reset(token)

    if individual_pack and _pack_covers_course(individual_pack.pack, course):
        return True

    # 7. Pack école actif (school) — vérifie le niveau de l'ÉLÈVE
    #    Suppress tenant filter — explicit school_id filter already scopes correctly.
    if user.school_id and user.niveau_scolaire:
        token = _tenant_filter_suppressed.set(True)
        try:
            school_pack = db.query(PackPurchase).join(StudyPack).filter(
                PackPurchase.school_id == user.school_id,
                PackPurchase.purchaser_type == "school",
                PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
                PackPurchase.valid_until > now,
                StudyPack.niveau_scolaire == user.niveau_scolaire,
                StudyPack.status == "published",
            ).first()
        finally:
            _tenant_filter_suppressed.reset(token)

        if school_pack and _pack_covers_course(school_pack.pack, course):
            return True

    # 8. ABAC: vérifie le tag_pack_requis via le système d'abonnement
    if check_abac_access(user, course, db):
        return True

    return False


def _pack_covers_course(pack: StudyPack, course: Course) -> bool:
    """
    Vérifie si un pack couvre un cours donné.
    Le niveau du cours doit correspondre au niveau du pack.
    Si pack.matieres est null → toutes les matières sont couvertes.
    Sinon → la matière du cours doit être dans la liste du pack.
    """
    if course.niveau_scolaire != pack.niveau_scolaire:
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
    required_level = TIER_HIERARCHY.get(tag_requis, 1)

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
    user_tier_level = TIER_HIERARCHY.get(pack_tier, 0)

    if user_tier_level < required_level:
        return False

    # Règle des matières : Basic et Silver vérifient la matière (Scolaire uniquement)
    if pack_tier in ("basic", "Basic", "silver", "Silver") and category_cible == "Scolaire":
        matieres_config = abonnement.pack.matieres if abonnement.pack else None
        if matieres_config:
            # matieres_config peut être une liste ou un dict avec clé "matieres"
            if isinstance(matieres_config, dict):
                matieres_list = matieres_config.get("matieres", [])
            elif isinstance(matieres_config, list):
                matieres_list = matieres_config
            else:
                matieres_list = []

            # Si des matières sont spécifiées, vérifie que la matière du cours y est
            if matieres_list and course.category:
                if course.category not in matieres_list:
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
    required_level = TIER_HIERARCHY.get(tag_requis, 1)

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
            detail=f"Accès requis : ce cours nécessite un abonnement {tag_requis}. "
                   f"Veuillez souscrire à un pack pour accéder à ce contenu.",
        )

    pack_tier = abonnement.pack.tier if abonnement.pack else "Basic"
    user_tier_level = TIER_HIERARCHY.get(pack_tier, 0)

    if user_tier_level < required_level:
        raise HTTPException(
            status_code=402,
            detail=f"Upgrade requis : ce cours nécessite un pack {tag_requis}. "
                   f"Votre pack actuel ({pack_tier}) ne couvre pas ce niveau.",
        )

    # Règle des matières (Scolaire uniquement)
    if pack_tier in ("basic", "Basic", "silver", "Silver") and category_cible == "Scolaire":
        matieres_config = abonnement.pack.matieres if abonnement.pack else None
        if matieres_config:
            if isinstance(matieres_config, dict):
                matieres_list = matieres_config.get("matieres", [])
            elif isinstance(matieres_config, list):
                matieres_list = matieres_config
            else:
                matieres_list = []

            if matieres_list and course.category:
                if course.category not in matieres_list:
                    raise HTTPException(
                        status_code=402,
                        detail=f"Matière non incluse : '{course.category}' n'est pas dans votre pack {pack_tier}. "
                               f"Matières disponibles : {', '.join(matieres_list)}",
                    )
    if pack.matieres is None:
        return True
    if not isinstance(pack.matieres, list):
        return True
    return course.category in pack.matieres


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
