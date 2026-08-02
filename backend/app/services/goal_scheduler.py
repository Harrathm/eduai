"""
Scheduler pour la génération automatique d'objectifs d'apprentissage.
Pré-génère les LearningGoal records pour les élèves excellence/etablissement.
"""
import logging
from datetime import date, datetime, timezone, timedelta

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


def _generate_monthly_goals_for_all_students():
    """
    Génère les objectifs monthly pour tous les élèves actifs
    des paliers excellence et etablissement.
    """
    from app.db.session import SessionLocal
    from app.models import User, UserRole
    from app.services.student_tier import get_student_tier
    from app.services.goal_tracking import generate_monthly_goal

    db = SessionLocal()
    try:
        students = db.query(User).filter(
            User.role == UserRole.STUDENT.value,
            User.is_active == True,
            User.is_approved == True,
        ).all()

        monthly_created = 0

        for student in students:
            tier = get_student_tier(student, db)
            if tier == "decouverte":
                continue

            monthly = generate_monthly_goal(student, db)
            if monthly and monthly.source == "auto_generated":
                monthly_created += 1

        if monthly_created:
            logger.info(f"Monthly goals generated: {monthly_created}")
    except Exception as e:
        logger.error(f"Error generating monthly goals: {e}")
    finally:
        db.close()


def _notify_expired_goals():
    """
    Vérifie les objectifs dont la période vient de se terminer
    et notifie les élèves (completed/missed).
    """
    from app.db.session import SessionLocal
    from app.models import LearningGoal
    from app.services.goal_tracking import compute_goal_status
    from app.services.notification_service import notify_goal_status

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # Objectifs dont la période se termine aujourd'hui ou hier
        recent_goals = db.query(LearningGoal).filter(
            LearningGoal.period_end <= now,
            LearningGoal.period_end >= now - timedelta(days=1),
        ).all()

        notified = 0
        for goal in recent_goals:
            status_data = compute_goal_status(goal, db)
            if status_data["status"] in ("completed", "missed"):
                # Vérifier si pas déjà notifié (flag dans la DB ou check doublon)
                from app.models import Message
                already = db.query(Message).filter(
                    Message.receiver_id == goal.user_id,
                    Message.subject.contains(f"Objectif {goal.horizon}"),
                ).first()
                if not already:
                    notify_goal_status(
                        goal.user_id,
                        goal.horizon,
                        status_data["status"],
                        status_data["progress_pct"],
                        db,
                    )
                    notified += 1

        if notified:
            logger.info(f"Goal notifications sent: {notified}")
    except Exception as e:
        logger.error(f"Error notifying expired goals: {e}")
    finally:
        db.close()


def start_goal_scheduler():
    """Démarre le planificateur de génération d'objectifs."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BackgroundScheduler()

        # Objectifs journaliers + hebdo : tous les jours à 00:05
        scheduler.add_job(
            _generate_goals_for_all_students,
            trigger=CronTrigger(hour=0, minute=5),
            id="daily_goal_generation",
            name="Génération des objectifs journaliers/hebdo",
            replace_existing=True,
        )

        # Objectifs mensuels : le 1er de chaque mois à 01:00
        scheduler.add_job(
            _generate_monthly_goals_for_all_students,
            trigger=CronTrigger(day=1, hour=1, minute=0),
            id="monthly_goal_generation",
            name="Génération des objectifs mensuels",
            replace_existing=True,
        )

        # Notifications objectifs expirés : tous les jours à 06:00
        scheduler.add_job(
            _notify_expired_goals,
            trigger=CronTrigger(hour=6, minute=0),
            id="goal_notification_check",
            name="Notification des objectifs expirés",
            replace_existing=True,
        )

        scheduler.start()
        logger.info("Planificateur d'objectifs démarré (daily + weekly + monthly + notifications)")
        return scheduler
    except ImportError:
        logger.warning("APScheduler non installé. Génération d'objectifs non automatique.")
        return None
