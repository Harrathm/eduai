"""
Service centralisé de vérification d'accès aux cours.
Vérifie l'accès via : gratuité, inscription, pack individuel, pack école.
Aucune inscription individuelle n'est créée pour un pack — l'accès est recalculé dynamiquement.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import (
    User, Course, CourseEnrollment, StudyPack, PackPurchase,
    PackPurchaseStatus, SchoolCourseAccess,
)

logger = logging.getLogger(__name__)


def has_course_access(user: User, course: Course, db: Session) -> bool:
    """
    Vérifie si un utilisateur a accès à un cours.
    Ordre de vérification :
      1. Cours gratuit (price=None ou 0) ou déjà acheté individuellement
      2. L'utilisateur est l'auteur du cours
      3. Inscription existante (CourseEnrollment)
      4. Accès école via SchoolCourseAccess
      5. Pack individuel actif (student) — niveau + matières correspondent
      6. Pack école actif (school) — niveau de l'ÉLÈVE + matières correspondent
    """
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

    # 4. Accès école via SchoolCourseAccess
    if user.school_id:
        sca = db.query(SchoolCourseAccess).filter(
            SchoolCourseAccess.school_id == user.school_id,
            SchoolCourseAccess.course_id == course.id,
            SchoolCourseAccess.is_active == True,
        ).first()
        if sca:
            return True

    # 5. Pack individuel actif (student)
    now = datetime.now(timezone.utc)
    individual_pack = db.query(PackPurchase).join(StudyPack).filter(
        PackPurchase.student_id == user.id,
        PackPurchase.purchaser_type == "student",
        PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
        PackPurchase.valid_until > now,
        StudyPack.niveau_scolaire == user.niveau_scolaire,
        StudyPack.status == "published",
    ).first()

    if individual_pack and _pack_covers_course(individual_pack.pack, course):
        return True

    # 6. Pack école actif (school) — vérifie le niveau de l'ÉLÈVE
    if user.school_id and user.niveau_scolaire:
        school_pack = db.query(PackPurchase).join(StudyPack).filter(
            PackPurchase.school_id == user.school_id,
            PackPurchase.purchaser_type == "school",
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
            StudyPack.niveau_scolaire == user.niveau_scolaire,
            StudyPack.status == "published",
        ).first()

        if school_pack and _pack_covers_course(school_pack.pack, course):
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
