"""
Scheduler pour la génération automatique d'objectifs d'apprentissage.
Pré-génère les LearningGoal records pour les élèves excellence/etablissement.
"""
import logging
from datetime import date

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _generate_goals_for_all_students():
    """
    Génère les objectifs daily/weekly pour tous les élèves actifs
    des paliers excellence et etablissement.
    """
    from app.db.session import SessionLocal
    from app.models import User, UserRole
    from app.services.student_tier import get_student_tier
    from app.services.goal_tracking import generate_daily_goal, generate_weekly_goal

    db = SessionLocal()
    try:
        students = db.query(User).filter(
            User.role == UserRole.STUDENT.value,
            User.is_active == True,
            User.is_approved == True,
        ).all()

        daily_created = 0
        weekly_created = 0

        for student in students:
            tier = get_student_tier(student, db)
            if tier == "decouverte":
                continue

            daily = generate_daily_goal(student, db)
            if daily and daily.source == "auto_generated":
                daily_created += 1

            weekly = generate_weekly_goal(student, db)
            if weekly and weekly.source == "auto_generated":
                weekly_created += 1

        if daily_created or weekly_created:
            logger.info(f"Goals generated: {daily_created} daily, {weekly_created} weekly")
    except Exception as e:
        logger.error(f"Error generating goals: {e}")
    finally:
        db.close()


def start_goal_scheduler():
    """Démarre le planificateur de génération d'objectifs."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BackgroundScheduler()

        # Objectifs journaliers : tous les jours à 00:05
        scheduler.add_job(
            _generate_goals_for_all_students,
            trigger=CronTrigger(hour=0, minute=5),
            id="daily_goal_generation",
            name="Génération des objectifs journaliers",
            replace_existing=True,
        )

        scheduler.start()
        logger.info("Planificateur d'objectifs démarré")
        return scheduler
    except ImportError:
        logger.warning("APScheduler non installé. Génération d'objectifs non automatique.")
        return None
