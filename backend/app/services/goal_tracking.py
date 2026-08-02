"""
Service de suivi d'objectifs pédagogiques — calcul dynamique du statut.
RÈGLE : le statut est TOUJOURS recalculé à partir des données réelles.
Jamais de cache persistant au-delà de quelques minutes en mémoire.
"""
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from typing import Optional
from functools import lru_cache
from collections import OrderedDict
import time

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    User, LearningGoal, LessonProgress, QuizAttempt,
    CourseEnrollment, Course, Module, Lesson,
    GoalHorizon, GoalStatus, GoalMetricType, GoalSource,
)
from app.services.student_tier import get_student_tier
from app.services.recommendation import get_recommended_path
from app.services.school_calendar import get_period_for_horizon

# ============================================================
# MESSAGES CONSTRUCTIFS (Phase 4, point 8)
# Un seul endroit dans toute l'application
# ============================================================

STATUS_MESSAGES = {
    GoalStatus.ON_TRACK.value: "Tu es sur la bonne voie !",
    GoalStatus.BEHIND.value: "Un peu de retard, mais rien d'impossible a rattraper.",
    GoalStatus.COMPLETED.value: "Objectif atteint — felicitations !",
    GoalStatus.MISSED.value: "Objectif non atteint cette fois — voici comment repartir.",
}


def get_status_message(status: str) -> str:
    return STATUS_MESSAGES.get(status, "")


# ============================================================
# CACHE COURT EN MEMOIE (5 min max, bounded to 1000 entries)
# ============================================================

_CACHE_TTL = 300  # 5 minutes
_CACHE_MAX_SIZE = 1000


class _TTLCache(OrderedDict):
    """Bounded dict with per-entry TTL. Evicts oldest entries when full."""

    def __init__(self, maxsize: int = _CACHE_MAX_SIZE, ttl: int = _CACHE_TTL):
        super().__init__()
        self._maxsize = maxsize
        self._ttl = ttl

    def get(self, key, default=None):
        if key in self:
            value, ts = super().__getitem__(key)
            if time.time() - ts < self._ttl:
                # Move to end (most recently accessed)
                self.move_to_end(key)
                return value
            # Expired — remove
            del self[key]
        return default

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        elif len(self) >= self._maxsize:
            # Evict oldest entry
            self.popitem(last=False)
        super().__setitem__(key, (value, time.time()))

    def __getitem__(self, key):
        result = self.get(key)
        if result is None and key not in self:
            raise KeyError(key)
        return result


_status_cache = _TTLCache()


def _get_cached_status(goal_id: int) -> Optional[str]:
    return _status_cache.get(goal_id)


def _set_cached_status(goal_id: int, status: str):
    _status_cache[goal_id] = status


# ============================================================
# CALCUL DE LA VALEUR ACTUELLE PAR METRIQUE
# ============================================================

def _compute_current_value(goal: LearningGoal, db: Session) -> float:
    """Calcule la valeur actuelle de la métrique sur la période du goal."""
    user = db.query(User).filter(User.id == goal.user_id).first()
    if not user:
        return 0.0

    start = goal.period_start
    end = goal.period_end

    if goal.metric_type == GoalMetricType.LESSONS_COMPLETED.value:
        return _count_lessons_completed(user, start, end, db)

    if goal.metric_type == GoalMetricType.QUIZ_AVERAGE_SCORE.value:
        return _quiz_average_score(user, start, end, db)

    if goal.metric_type == GoalMetricType.STUDY_TIME_MINUTES.value:
        return _study_time_minutes(user, start, end, db)

    if goal.metric_type == GoalMetricType.CHAPTER_COMPLETION.value:
        return _chapter_completion_count(user, start, end, db)

    if goal.metric_type == GoalMetricType.CURRICULUM_COVERAGE_PERCENT.value:
        return _curriculum_coverage_percent(user, start, end, db)

    return 0.0


def _count_lessons_completed(user: User, start: datetime, end: datetime, db: Session) -> float:
    enrollment_ids = [e.id for e in db.query(CourseEnrollment.id).filter(
        CourseEnrollment.student_id == user.id,
    ).all()]

    if not enrollment_ids:
        return 0.0

    return float(db.query(LessonProgress).filter(
        LessonProgress.enrollment_id.in_(enrollment_ids),
        LessonProgress.status == "completed",
        LessonProgress.completed_at >= start,
        LessonProgress.completed_at <= end,
    ).count())


def _quiz_average_score(user: User, start: datetime, end: datetime, db: Session) -> float:
    result = db.query(func.avg(QuizAttempt.score_percent)).filter(
        QuizAttempt.student_id == user.id,
        QuizAttempt.status == "completed",
        QuizAttempt.completed_at >= start,
        QuizAttempt.completed_at <= end,
    ).scalar()
    return float(result) if result else 0.0


def _study_time_minutes(user: User, start: datetime, end: datetime, db: Session) -> float:
    enrollment_ids = [e.id for e in db.query(CourseEnrollment.id).filter(
        CourseEnrollment.student_id == user.id,
    ).all()]

    if not enrollment_ids:
        return 0.0

    total_seconds = db.query(func.sum(LessonProgress.time_spent_seconds)).filter(
        LessonProgress.enrollment_id.in_(enrollment_ids),
        LessonProgress.started_at >= start,
        LessonProgress.started_at <= end,
    ).scalar()
    return float(total_seconds or 0) / 60.0


def _chapter_completion_count(user: User, start: datetime, end: datetime, db: Session) -> float:
    """Nombre de modules où TOUTES les leçons sont complétées."""
    enrollment_ids = [e.id for e in db.query(CourseEnrollment.id).filter(
        CourseEnrollment.student_id == user.id,
    ).all()]

    if not enrollment_ids:
        return 0.0

    completed_modules = 0
    course_ids = [e.course_id for e in db.query(CourseEnrollment).filter(
        CourseEnrollment.id.in_(enrollment_ids),
    ).all()]

    for course_id in course_ids:
        modules = db.query(Module).filter(Module.course_id == course_id).all()
        for module in modules:
            total_lessons = db.query(Lesson).filter(Lesson.module_id == module.id).count()
            if total_lessons == 0:
                continue
            completed = db.query(LessonProgress).filter(
                LessonProgress.enrollment_id.in_(enrollment_ids),
                LessonProgress.lesson_id.in_(
                    db.query(Lesson.id).filter(Lesson.module_id == module.id)
                ),
                LessonProgress.status == "completed",
            ).count()
            if completed >= total_lessons:
                completed_modules += 1

    return float(completed_modules)


def _curriculum_coverage_percent(user: User, start: datetime, end: datetime, db: Session) -> float:
    """Pourcentage de leçons complétées sur l'ensemble des cours inscrits."""
    enrollment_ids = [e.id for e in db.query(CourseEnrollment.id).filter(
        CourseEnrollment.student_id == user.id,
    ).all()]

    if not enrollment_ids:
        return 0.0

    total_lessons = db.query(Lesson).join(Module).join(Course).filter(
        Course.id.in_(
            db.query(CourseEnrollment.course_id).filter(
                CourseEnrollment.id.in_(enrollment_ids)
            )
        )
    ).count()

    if total_lessons == 0:
        return 0.0

    completed = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id.in_(enrollment_ids),
        LessonProgress.status == "completed",
        LessonProgress.completed_at >= start,
        LessonProgress.completed_at <= end,
    ).count()

    return round((completed / total_lessons) * 100, 1)


# ============================================================
# CALCUL DU STATUT
# ============================================================

def compute_goal_status(goal: LearningGoal, db: Session) -> dict:
    """
    Calcule le statut d'un objectif en temps réel.
    Retourne: {"status": str, "current_value": float, "target_value": float,
               "progress_pct": float, "message": str, "days_remaining": int}
    """
    cached = _get_cached_status(goal.id)
    # On ne cache que le statut brut, pas les détails

    now = datetime.now(timezone.utc)
    current_value = _compute_current_value(goal, db)
    target_value = float(goal.target_value)

    # Calcul du pourcentage de progression
    if target_value > 0:
        progress_pct = min(round((current_value / target_value) * 100, 1), 100.0)
    else:
        progress_pct = 100.0 if current_value > 0 else 0.0

    # Période dépassée ?
    period_end_dt = goal.period_end.replace(tzinfo=timezone.utc) if goal.period_end.tzinfo is None else goal.period_end
    period_start_dt = goal.period_start.replace(tzinfo=timezone.utc) if goal.period_start.tzinfo is None else goal.period_start
    period_duration = (period_end_dt - period_start_dt).total_seconds()

    if now > period_end_dt:
        # Période terminée
        if current_value >= target_value:
            status = GoalStatus.COMPLETED.value
        else:
            status = GoalStatus.MISSED.value
    else:
        # Période en cours — vérifier le rythme
        elapsed = (now - period_start_dt).total_seconds()
        if period_duration > 0:
            expected_ratio = elapsed / period_duration
        else:
            expected_ratio = 1.0

        expected_value = target_value * expected_ratio
        # Tolérance de 10% en dessous du rythme attendu
        if current_value >= expected_value * 0.9:
            status = GoalStatus.ON_TRACK.value
        else:
            status = GoalStatus.BEHIND.value

    days_remaining = max(0, (period_end_dt - now).days)
    message = get_status_message(status)

    return {
        "status": status,
        "current_value": round(current_value, 2),
        "target_value": target_value,
        "progress_pct": progress_pct,
        "message": message,
        "days_remaining": days_remaining,
    }


# ============================================================
# GENERATION AUTOMATIQUE D'OBJECTIFS
# ============================================================

def generate_daily_goal(user: User, db: Session) -> Optional[LearningGoal]:
    """
    Génère un objectif journalier pour les paliers excellence/etablissement.
    Retourne None pour decouverte (pas d'objectif personnalisé).
    """
    tier = get_student_tier(user, db)
    if tier == "decouverte":
        return None

    today = date.today()
    period_start, period_end = get_period_for_horizon("daily", today)

    # Vérifier si un objectif daily existe déjà pour aujourd'hui
    start_dt = datetime.combine(period_start, datetime.min.time())
    end_dt = datetime.combine(period_end, datetime.max.time())
    existing = db.query(LearningGoal).filter(
        LearningGoal.user_id == user.id,
        LearningGoal.horizon == GoalHorizon.DAILY.value,
        LearningGoal.period_start >= start_dt,
        LearningGoal.period_start <= end_dt,
    ).first()
    if existing:
        return existing

    # Objectif par défaut : 2 leçons complétées
    goal = LearningGoal(
        user_id=user.id,
        matiere=None,  # transversal
        horizon=GoalHorizon.DAILY.value,
        metric_type=GoalMetricType.LESSONS_COMPLETED.value,
        target_value=Decimal("2"),
        period_start=start_dt,
        period_end=end_dt,
        source=GoalSource.AUTO_GENERATED.value,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def generate_weekly_goal(user: User, db: Session, target_hours: float = 5.0) -> Optional[LearningGoal]:
    """
    Génère un objectif hebdomadaire pour les paliers excellence/etablissement.
    Retourne None pour decouverte.
    target_hours : temps d'étude cible par défaut 5h/semaine.
    """
    tier = get_student_tier(user, db)
    if tier == "decouverte":
        return None

    today = date.today()
    period_start, period_end = get_period_for_horizon("weekly", today)

    start_dt = datetime.combine(period_start, datetime.min.time())
    end_dt = datetime.combine(period_end, datetime.max.time())
    existing = db.query(LearningGoal).filter(
        LearningGoal.user_id == user.id,
        LearningGoal.horizon == GoalHorizon.WEEKLY.value,
        LearningGoal.period_start >= start_dt,
        LearningGoal.period_start <= end_dt,
    ).first()
    if existing:
        return existing

    goal = LearningGoal(
        user_id=user.id,
        matiere=None,
        horizon=GoalHorizon.WEEKLY.value,
        metric_type=GoalMetricType.STUDY_TIME_MINUTES.value,
        target_value=Decimal(str(target_hours * 60)),  # Convertir en minutes
        period_start=start_dt,
        period_end=end_dt,
        source=GoalSource.AUTO_GENERATED.value,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def generate_monthly_goal(user: User, db: Session) -> Optional[LearningGoal]:
    """
    Génère un objectif mensuel pour les paliers excellence/etablissement.
    Retourne None pour decouverte.
    Objectif par défaut : 10 leçons complétées + 20% de couverture curriculum.
    """
    tier = get_student_tier(user, db)
    if tier == "decouverte":
        return None

    today = date.today()
    period_start, period_end = get_period_for_horizon("monthly", today)

    start_dt = datetime.combine(period_start, datetime.min.time())
    end_dt = datetime.combine(period_end, datetime.max.time())
    existing = db.query(LearningGoal).filter(
        LearningGoal.user_id == user.id,
        LearningGoal.horizon == GoalHorizon.MONTHLY.value,
        LearningGoal.period_start >= start_dt,
        LearningGoal.period_start <= end_dt,
    ).first()
    if existing:
        return existing

    goal = LearningGoal(
        user_id=user.id,
        matiere=None,
        horizon=GoalHorizon.MONTHLY.value,
        metric_type=GoalMetricType.LESSONS_COMPLETED.value,
        target_value=Decimal("10"),
        period_start=start_dt,
        period_end=end_dt,
        source=GoalSource.AUTO_GENERATED.value,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def ensure_goals_exist(user: User, db: Session) -> dict:
    """
    S'assure que les objectifs daily, weekly et monthly existent pour l'utilisateur.
    Appelé au login ou au chargement du dashboard.
    Retourne les objectifs créés/récupérés.
    """
    daily = generate_daily_goal(user, db)
    weekly = generate_weekly_goal(user, db)
    monthly = generate_monthly_goal(user, db)
    return {
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
    }
