"""
Tâche planifiée : calcul mensuel du Revenue Share pour les Teacher Partners.
S'exécute le 1er de chaque mois à 02h00 pour le mois écoulé.

Logique choisie : Montant fixe par vue d'élève premium.
"""
import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import delete, func, and_, or_

from app.db import SessionLocal
from app.models import (
    User, Course, Lesson, CourseEnrollment, LessonProgress,
    Abonnement, PackDefinition, TeacherRevenueLedger,
)

logger = logging.getLogger(__name__)

# Montant fixe par vue d'un élève premium
REVENUE_PER_VIEW_TND = Decimal("0.05")


def calculate_monthly_teacher_revenue(
    db,
    target_month: Optional[date] = None,
) -> int:
    """
    Calcule le revenue share mensuel pour tous les Teacher Partners.

    Args:
        db: Session SQLAlchemy
        target_month: Mois cible (1er du mois). Si None, mois écoulé.

    Returns:
        Nombre de lignes insérées/mises à jour dans teacher_revenue_ledger.
    """
    if target_month is None:
        today = date.today()
        target_month = date(today.year, today.month, 1)

    # Début et fin du mois cible
    if target_month.month == 12:
        month_end = date(target_month.year + 1, 1, 1)
    else:
        month_end = date(target_month.year, target_month.month + 1, 1)

    logger.info(
        "Revenue Share: début du calcul pour %s (période %s → %s)",
        target_month.isoformat(), target_month.isoformat(), month_end.isoformat(),
    )

    # 1. Identifier tous les Teacher Partners actifs
    partners = db.query(User).filter(
        User.is_partner == True,  # noqa: E712
        User.is_active == True,  # noqa: E712
    ).all()

    if not partners:
        logger.info("Revenue Share: aucun Teacher Partner actif trouvé.")
        return 0

    partner_ids = {p.id for p in partners}
    logger.info("Revenue Share: %d partner(s) trouvé(s): %s", len(partners), partner_ids)

    # 2. IDs des élèves ayant un abonnement actif ou en grace pendant le mois cible
    premium_student_ids = set(
        row[0] for row in db.query(Abonnement.user_id).join(PackDefinition).filter(
            Abonnement.statut.in_(["actif", "grace"]),
            PackDefinition.tier.in_(["Basic", "Silver", "Golden"]),
            Abonnement.debut < month_end,
            or_(
                Abonnement.fin >= target_month,
                Abonnement.grace_fin >= target_month,
            ),
        ).distinct().all()
    )

    if not premium_student_ids:
        logger.info("Revenue Share: aucun élève premium durant %s.", target_month.isoformat())
        return 0

    logger.info(
        "Revenue Share: %d élève(s) premium identifié(s) pour %s",
        len(premium_student_ids), target_month.isoformat(),
    )

    # 3. Compter les vues uniques (teacher, lesson, student) durant le mois
    #    Jointure : LessonProgress → CourseEnrollment → User (student)
    #               LessonProgress → Lesson → User (teacher partner)
    views_query = (
        db.query(
            Lesson.teacher_id,
            LessonProgress.lesson_id,
            func.count(func.distinct(CourseEnrollment.student_id)).label("unique_views"),
        )
        .join(CourseEnrollment, CourseEnrollment.id == LessonProgress.enrollment_id)
        .join(Lesson, Lesson.id == LessonProgress.lesson_id)
        .filter(
            Lesson.teacher_id.in_(partner_ids),
            CourseEnrollment.student_id.in_(premium_student_ids),
            LessonProgress.status.in_(["in_progress", "completed"]),
            # Filtre temporel sur started_at ou completed_at
            or_(
                and_(
                    LessonProgress.started_at >= target_month,
                    LessonProgress.started_at < month_end,
                ),
                and_(
                    LessonProgress.completed_at >= target_month,
                    LessonProgress.completed_at < month_end,
                ),
            ),
        )
        .group_by(Lesson.teacher_id, LessonProgress.lesson_id)
        .all()
    )

    if not views_query:
        logger.info("Revenue Share: aucune vue enregistrée pour %s.", target_month.isoformat())
        return 0

    logger.info("Revenue Share: %d combinaison(s) (teacher, lesson) trouvée(s).", len(views_query))

    # 4. Supprimer les anciennes lignes du mois avant réinsertion (évite les doublons)
    db.execute(
        delete(TeacherRevenueLedger).where(
            TeacherRevenueLedger.period_month == target_month,
        )
    )
    db.flush()

    # 5. Insérer les nouvelles lignes
    inserted = 0
    for teacher_id, lesson_id, unique_views in views_query:
        revenue = Decimal(str(unique_views)) * REVENUE_PER_VIEW_TND
        entry = TeacherRevenueLedger(
            teacher_id=teacher_id,
            lesson_id=lesson_id,
            consumption_count=unique_views,
            revenue_amount=revenue.quantize(Decimal("0.01")),
            period_month=target_month,
        )
        db.add(entry)
        inserted += 1

    db.commit()

    logger.info(
        "Revenue Share: %d ligne(s) insérée(s) pour %s (taux: %s TND/vue).",
        inserted, target_month.isoformat(), REVENUE_PER_VIEW_TND,
    )
    return inserted


def run_monthly_revenue_calculation():
    """
    Point d'entrée pour le scheduler APScheduler.
    Calcule les revenus du mois écoulé.
    """
    logger.info("=== Revenue Share Cron: démarrage ===")
    db = SessionLocal()
    try:
        today = date.today()
        # Calculer le mois écoulé
        if today.month == 1:
            target = date(today.year - 1, 12, 1)
        else:
            target = date(today.year, today.month - 1, 1)

        count = calculate_monthly_teacher_revenue(db, target)
        logger.info("=== Revenue Share Cron: terminé — %d ligne(s) écrite(s) ===", count)
    except Exception as e:
        logger.error("=== Revenue Share Cron: ERREUR — %s ===", e, exc_info=True)
    finally:
        db.close()


def start_revenue_share_scheduler():
    """Démarre le planificateur de calcul du Revenue Share."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BackgroundScheduler()

        # Calcul mensuel : le 1er de chaque mois à 02h00
        scheduler.add_job(
            run_monthly_revenue_calculation,
            trigger=CronTrigger(day=1, hour=2, minute=0),
            id="monthly_revenue_share",
            name="Calcul mensuel du Revenue Share (Teacher Partners)",
            replace_existing=True,
        )

        scheduler.start()
        logger.info(
            "Planificateur Revenue Share démarré "
            "(mensuel le 1er à 02h00, taux=%s TND/vue)",
            REVENUE_PER_VIEW_TND,
        )
        return scheduler
    except ImportError:
        logger.warning(
            "APScheduler non installé. Le calcul du Revenue Share ne sera pas automatique."
        )
        return None
