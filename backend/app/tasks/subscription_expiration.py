"""
Tâche de planification pour l'expiration automatique des abonnements.
Vérifie périodiquement les abonnements expirés et les désactive.
"""

import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import SessionLocal
from app.models import Subscription

logger = logging.getLogger(__name__)


def check_expired_subscriptions():
    """Vérifie et désactive les abonnements expirés."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        expired_subs = db.query(Subscription).filter(
            Subscription.is_active == True,
            Subscription.ends_at != None,
            Subscription.ends_at < now
        ).all()
        
        count = 0
        for sub in expired_subs:
            sub.status = "expired"
            sub.is_active = False
            count += 1
            logger.info(f"Abonnement expiré désactivé: school_id={sub.school_id}, sub_id={sub.id}")
        
        if count > 0:
            db.commit()
            logger.info(f"{count} abonnement(s) expiré(s) désactivé(s)")
        
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la vérification des abonnements expirés: {e}")
        raise
    finally:
        db.close()


def start_scheduler():
    """Démarre le planificateur de vérification des abonnements."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            check_expired_subscriptions,
            trigger=IntervalTrigger(hours=1),
            id="subscription_expiration_check",
            name="Vérification des abonnements expirés",
            replace_existing=True
        )
        scheduler.start()
        logger.info("Planificateur d'expiration des abonnements démarré")
        return scheduler
    except ImportError:
        logger.warning("APScheduler non installé. La vérification des abonnements expirés ne sera pas automatique.")
        return None
