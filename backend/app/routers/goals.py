"""
Router de suivi d'objectifs pédagogiques — 5 horizons temporels.
Endpoints:
  Learner:
    - GET  /learner/goals?horizon=...       — objectifs avec statut calculé
    - GET  /learner/goals/summary           — synthèse 5 horizons
    - GET  /learner/goals/report            — bilan de fin de période
    - POST /learner/goals/monthly           — objectif mensuel (élève ou teacher/ped lead)
    - POST /learner/goals/annual            — objectif annuel (élève ou pedagogical_lead)

  Pedagogical Lead:
    - POST /pedagogical-lead/goals/quarterly      — assigner objectif trimestriel à une classe
    - GET  /pedagogical-lead/goals/quarterly-overview — vue agrégée par classe/élève
"""
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.auth import get_current_user
from app.deps import require_pedagogical_lead, check_school_access
from app.models import (
    User, LearningGoal, ClassRoom, ClassroomEnrollment,
    GoalHorizon, GoalStatus, GoalMetricType, GoalSource,
)
from app.services.goal_tracking import (
    compute_goal_status, ensure_goals_exist, get_status_message,
)
from app.services.school_calendar import get_period_for_horizon, get_current_trimester
from app.services.student_tier import get_student_tier

# ============================================================
# Learner Router
# ============================================================

learner_router = APIRouter(prefix="/learner", tags=["Learner Goals"])


@learner_router.get("/goals")
def list_goals(
    horizon: Optional[str] = Query(None, description="daily, weekly, monthly, quarterly, annual"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les objectifs de l'élève avec statut calculé en temps réel.
    Si horizon est spécifié, retourne uniquement l'objectif de cet horizon.
    """
    query = db.query(LearningGoal).filter(
        LearningGoal.user_id == current_user.id,
    )
    if horizon:
        query = query.filter(LearningGoal.horizon == horizon)

    goals = query.order_by(LearningGoal.period_start.desc()).all()

    results = []
    for goal in goals:
        status_data = compute_goal_status(goal, db)
        results.append({
            "id": goal.id,
            "matiere": goal.matiere,
            "horizon": goal.horizon,
            "metric_type": goal.metric_type,
            "target_value": float(goal.target_value),
            "period_start": goal.period_start.isoformat(),
            "period_end": goal.period_end.isoformat(),
            "source": goal.source,
            **status_data,
        })

    return results


@learner_router.get("/goals/summary")
def goals_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les 5 horizons en une seule réponse — optimisé pour le dashboard.
    Priorité : daily > weekly > monthly > quarterly > annual.
    """
    # S'assurer que daily et weekly existent
    ensure_goals_exist(current_user, db)

    horizons_order = ["daily", "weekly", "monthly", "quarterly", "annual"]
    summary = {}

    for h in horizons_order:
        goal = db.query(LearningGoal).filter(
            LearningGoal.user_id == current_user.id,
            LearningGoal.horizon == h,
        ).order_by(LearningGoal.period_start.desc()).first()

        if goal:
            status_data = compute_goal_status(goal, db)
            summary[h] = {
                "id": goal.id,
                "matiere": goal.matiere,
                "metric_type": goal.metric_type,
                "target_value": float(goal.target_value),
                "period_start": goal.period_start.isoformat(),
                "period_end": goal.period_end.isoformat(),
                **status_data,
            }
        else:
            summary[h] = None

    return summary


@learner_router.get("/goals/report")
def period_report(
    horizon: str = Query(..., description="weekly, monthly, quarterly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bilan de fin de période — récapitulatif consolidé.
    Accessible à l'élève, à son enseignant et au pedagogical_lead.
    """
    if horizon not in ("weekly", "monthly", "quarterly"):
        raise HTTPException(status_code=400, detail="Horizon doit etre weekly, monthly ou quarterly")

    goals = db.query(LearningGoal).filter(
        LearningGoal.user_id == current_user.id,
        LearningGoal.horizon == horizon,
    ).order_by(LearningGoal.period_start.desc()).all()

    if not goals:
        return {"horizon": horizon, "goals": [], "summary": "Aucun objectif pour cette periode."}

    goal_statuses = []
    completed_count = 0
    missed_count = 0
    on_track_count = 0
    behind_count = 0

    for goal in goals:
        status_data = compute_goal_status(goal, db)
        goal_statuses.append({
            "id": goal.id,
            "matiere": goal.matiere,
            "metric_type": goal.metric_type,
            "target_value": float(goal.target_value),
            **status_data,
        })
        s = status_data["status"]
        if s == GoalStatus.COMPLETED.value:
            completed_count += 1
        elif s == GoalStatus.MISSED.value:
            missed_count += 1
        elif s == GoalStatus.ON_TRACK.value:
            on_track_count += 1
        elif s == GoalStatus.BEHIND.value:
            behind_count += 1

    total = len(goals)
    attainment_rate = round((completed_count / total) * 100, 1) if total > 0 else 0.0

    return {
        "horizon": horizon,
        "period": {
            "start": goals[0].period_start.isoformat() if goals else None,
            "end": goals[0].period_end.isoformat() if goals else None,
        },
        "goals": goal_statuses,
        "stats": {
            "total": total,
            "completed": completed_count,
            "missed": missed_count,
            "on_track": on_track_count,
            "behind": behind_count,
            "attainment_rate": attainment_rate,
        },
        "summary": f"{completed_count}/{total} objectifs atteints ({attainment_rate}%)",
    }


@learner_router.post("/goals/annual")
def create_annual_goal(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crée un objectif annuel — par l'élève lui-même ou par un pedagogical_lead.
    Body: {"matiere": "...", "target_value": 80, "metric_type": "curriculum_coverage_percent"}
    """
    # Vérifier si l'utilisateur a les droits pour créer pour un autre
    target_user_id = body.get("user_id", current_user.id)
    if target_user_id != current_user.id:
        # Seul un pedagogical_lead peut créer pour un autre
        if current_user.role not in ("pedagogical_lead", "super_admin"):
            raise HTTPException(status_code=403, detail="Non autorise")

    matiere = body.get("matiere")
    metric_type = body.get("metric_type", GoalMetricType.CURRICULUM_COVERAGE_PERCENT.value)
    target_value = body.get("target_value", 80)

    period_start, period_end = get_period_for_horizon("annual")
    start_dt = datetime.combine(period_start, datetime.min.time())
    end_dt = datetime.combine(period_end, datetime.max.time())

    # Vérifier si un objectif annual existe déjà
    existing = db.query(LearningGoal).filter(
        LearningGoal.user_id == target_user_id,
        LearningGoal.horizon == GoalHorizon.ANNUAL.value,
    ).first()
    if existing:
        existing.target_value = Decimal(str(target_value))
        existing.metric_type = metric_type
        existing.matiere = matiere
        db.commit()
        db.refresh(existing)
        return {"id": existing.id, "message": "Objectif annual mis a jour"}

    source = GoalSource.STUDENT_SELF.value if target_user_id == current_user.id else GoalSource.PEDAGOGICAL_LEAD_ASSIGNED.value

    goal = LearningGoal(
        user_id=target_user_id,
        matiere=matiere,
        horizon=GoalHorizon.ANNUAL.value,
        metric_type=metric_type,
        target_value=Decimal(str(target_value)),
        period_start=start_dt,
        period_end=end_dt,
        source=source,
        created_by=current_user.id,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return {"id": goal.id, "message": "Objectif annual cree"}


@learner_router.post("/goals/monthly")
def create_monthly_goal(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crée un objectif mensuel — par l'élève lui-même ou par un pedagogical_lead.
    Body: {"matiere": "...", "target_value": 10, "metric_type": "lessons_completed"}
    """
    target_user_id = body.get("user_id", current_user.id)
    if target_user_id != current_user.id:
        if current_user.role not in ("pedagogical_lead", "super_admin", "teacher"):
            raise HTTPException(status_code=403, detail="Non autorise")

    matiere = body.get("matiere")
    metric_type = body.get("metric_type", GoalMetricType.LESSONS_COMPLETED.value)
    target_value = body.get("target_value", 10)

    period_start, period_end = get_period_for_horizon("monthly")
    start_dt = datetime.combine(period_start, datetime.min.time())
    end_dt = datetime.combine(period_end, datetime.max.time())

    existing = db.query(LearningGoal).filter(
        LearningGoal.user_id == target_user_id,
        LearningGoal.horizon == GoalHorizon.MONTHLY.value,
        LearningGoal.matiere == matiere,
        LearningGoal.period_start == start_dt,
    ).first()
    if existing:
        existing.target_value = Decimal(str(target_value))
        existing.metric_type = metric_type
        db.commit()
        db.refresh(existing)
        return {"id": existing.id, "message": "Objectif monthly mis a jour"}

    source = GoalSource.STUDENT_SELF.value if target_user_id == current_user.id else GoalSource.PEDAGOGICAL_LEAD_ASSIGNED.value

    goal = LearningGoal(
        user_id=target_user_id,
        matiere=matiere,
        horizon=GoalHorizon.MONTHLY.value,
        metric_type=metric_type,
        target_value=Decimal(str(target_value)),
        period_start=start_dt,
        period_end=end_dt,
        source=source,
        created_by=current_user.id,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return {"id": goal.id, "message": "Objectif monthly cree"}


# ============================================================
# Pedagogical Lead Router
# ============================================================

pedagogical_lead_router = APIRouter(prefix="/pedagogical-lead", tags=["Pedagogical Lead Goals"])


class QuarterlyGoalRequest(BaseModel):
    classroom_id: int
    matiere: Optional[str] = None
    metric_type: str = "curriculum_coverage_percent"
    target_value: float = 80


@pedagogical_lead_router.post("/goals/quarterly")
def assign_quarterly_class_goal(
    body: QuarterlyGoalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_lead),
):
    """
    Assigne un objectif trimestriel à TOUTE une classe en une fois.
    Appliqué à chaque élève de la classe.
    """
    classroom = db.query(ClassRoom).filter(ClassRoom.id == body.classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classe introuvable")

    check_school_access(current_user, classroom.school_id)

    tri = get_current_trimester()
    if not tri:
        raise HTTPException(status_code=400, detail="Pas de trimestre actif")

    start_dt = datetime.combine(tri.start, datetime.min.time())
    end_dt = datetime.combine(tri.end, datetime.max.time())

    # Récupérer tous les élèves de la classe
    student_ids = [e.student_id for e in db.query(ClassroomEnrollment).filter(
        ClassroomEnrollment.classroom_id == body.classroom_id,
    ).all()]

    if not student_ids:
        raise HTTPException(status_code=400, detail="Aucun eleve dans cette classe")

    created = 0
    updated = 0
    for sid in student_ids:
        existing = db.query(LearningGoal).filter(
            LearningGoal.user_id == sid,
            LearningGoal.horizon == GoalHorizon.QUARTERLY.value,
            LearningGoal.matiere == body.matiere,
            LearningGoal.period_start == start_dt,
        ).first()

        if existing:
            existing.target_value = Decimal(str(body.target_value))
            existing.metric_type = body.metric_type
            updated += 1
        else:
            goal = LearningGoal(
                user_id=sid,
                matiere=body.matiere,
                horizon=GoalHorizon.QUARTERLY.value,
                metric_type=body.metric_type,
                target_value=Decimal(str(body.target_value)),
                period_start=start_dt,
                period_end=end_dt,
                source=GoalSource.PEDAGOGICAL_LEAD_ASSIGNED.value,
                created_by=current_user.id,
            )
            db.add(goal)
            created += 1

    db.commit()
    return {
        "message": f"Objectif trimestriel assigne a {len(student_ids)} eleves",
        "created": created,
        "updated": updated,
        "classroom": classroom.name,
        "trimester": tri.number,
    }


@pedagogical_lead_router.get("/goals/quarterly-overview")
def quarterly_overview(
    classroom_id: Optional[int] = Query(None, description="Filtrer par classe"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_lead),
):
    """
    Vue agrégée des objectifs trimestriels — toutes les classes de l'école.
    Retourne le statut calculé de chaque élève.
    """
    tri = get_current_trimester()
    if not tri:
        return {"error": "Pas de trimestre actif", "students": []}

    start_dt = datetime.combine(tri.start, datetime.min.time())
    end_dt = datetime.combine(tri.end, datetime.max.time())

    # Récupérer les classes de l'école
    query = db.query(ClassRoom).filter(ClassRoom.school_id == current_user.school_id)
    if classroom_id:
        query = query.filter(ClassRoom.id == classroom_id)

    classrooms = query.all()
    result = []

    for classroom in classrooms:
        student_ids = [e.student_id for e in db.query(ClassroomEnrollment).filter(
            ClassroomEnrollment.classroom_id == classroom.id,
        ).all()]

        students_data = []
        for sid in student_ids:
            goals = db.query(LearningGoal).filter(
                LearningGoal.user_id == sid,
                LearningGoal.horizon == GoalHorizon.QUARTERLY.value,
                LearningGoal.period_start == start_dt,
            ).all()

            goal_statuses = []
            for g in goals:
                status_data = compute_goal_status(g, db)
                goal_statuses.append({
                    "matiere": g.matiere,
                    "metric_type": g.metric_type,
                    "target_value": float(g.target_value),
                    **status_data,
                })

            students_data.append({
                "student_id": sid,
                "goals": goal_statuses,
            })

        result.append({
            "classroom_id": classroom.id,
            "classroom_name": classroom.name,
            "trimester": tri.number,
            "students": students_data,
        })

    return {"trimester": tri.number, "classrooms": result}
