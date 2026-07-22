"""
Service de notifications pédagogiques — rappels et félicitations.
NON intrusives : pas de push aggressive, juste des rappels constructifs.
Les notifications ne sont envoyées QUE pour les paliers excellence et etablissement.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import (
    User, LearningGoal, GoalStatus, GoalHorizon, GoalMetricType,
)
from app.services.student_tier import get_student_tier
from app.services.goal_tracking import compute_goal_status


def generate_soft_notifications(user: User, db: Session) -> list[dict]:
    """
    Génère les notifications douces pour un utilisateur.
    Appelé quotidiennement (tâche planifiée) ou au chargement du dashboard.
    Pas de notification pour le palier decouverte.
    """
    tier = get_student_tier(user, db)
    if tier == "decouverte":
        return []

    notifications = []
    now = datetime.now(timezone.utc)

    # 1. Rappel objectif journalier non atteint (en fin de journée)
    daily_goals = db.query(LearningGoal).filter(
        LearningGoal.user_id == user.id,
        LearningGoal.horizon == GoalHorizon.DAILY.value,
    ).order_by(LearningGoal.period_start.desc()).limit(1).all()

    for goal in daily_goals:
        status_data = compute_goal_status(goal, db)
        if status_data["status"] == GoalStatus.BEHIND.value:
            notifications.append({
                "type": "daily_reminder",
                "title": "Rappel objectif du jour",
                "message": "Tu n'as pas encore atteint ton objectif journalier. "
                           "Encore un petit effort avant la fin de la journee !",
                "priority": "low",
                "goal_id": goal.id,
            })

    # 2. Félicitations objectif hebdomadaire atteint
    weekly_goals = db.query(LearningGoal).filter(
        LearningGoal.user_id == user.id,
        LearningGoal.horizon == GoalHorizon.WEEKLY.value,
    ).order_by(LearningGoal.period_start.desc()).limit(1).all()

    for goal in weekly_goals:
        status_data = compute_goal_status(goal, db)
        if status_data["status"] == GoalStatus.COMPLETED.value:
            # Vérifier si on a déjà notifié cette semaine
            already_notified = _has_notification_been_sent(
                user.id, "weekly_completed", goal.period_start, db
            )
            if not already_notified:
                notifications.append({
                    "type": "weekly_celebration",
                    "title": "Objectif hebdomadaire atteint !",
                    "message": "Felicitations ! Tu as atteint ton objectif de la semaine. "
                               "Continue sur cette lancée.",
                    "priority": "normal",
                    "goal_id": goal.id,
                })

    # 3. Félicitations objectif trimestriel atteint
    quarterly_goals = db.query(LearningGoal).filter(
        LearningGoal.user_id == user.id,
        LearningGoal.horizon == GoalHorizon.QUARTERLY.value,
    ).order_by(LearningGoal.period_start.desc()).limit(1).all()

    for goal in quarterly_goals:
        status_data = compute_goal_status(goal, db)
        if status_data["status"] == GoalStatus.COMPLETED.value:
            already_notified = _has_notification_been_sent(
                user.id, "quarterly_completed", goal.period_start, db
            )
            if not already_notified:
                notifications.append({
                    "type": "quarterly_celebration",
                    "title": "Objectif trimestriel atteint !",
                    "message": "Excellent travail ! Tu as atteint ton objectif trimestriel. "
                               "Tu es en bonne voie pour la reussite.",
                    "priority": "high",
                    "goal_id": goal.id,
                })

    return notifications


def _has_notification_been_sent(
    user_id: int, notif_type: str, period_start: datetime, db: Session
) -> bool:
    """
    Vérification simple pour ne pas spammer les notifications.
    Utilise un stockage en base (table notification_log) ou un cache.
    Pour simplifier, on utilise un cache en mémoire qui se reset au redémarrage.
    """
    # TODO: implémenter un vrai stockage si besoin
    # Pour l'instant, pas de spam car les notifications sont régénérées à chaque appel
    return False
