"""Gamification — badges, streaks, classements API."""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import User, StudentBadge, StudentStreak, StudentRanking, BadgeDefinition
from app.schemas import StudentBadgeRead, StudentStreakRead, StudentRankingRead
from app.services.gamification import (
    check_and_award_badges,
    record_daily_streak,
    get_current_streak,
    compute_rankings,
)
from app.services.student_tier import get_student_tier

router = APIRouter()


@router.get("/badges")
def get_my_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Liste les badges de l'élève avec les badges non obtenus."""
    all_badges = db.query(BadgeDefinition).order_by(BadgeDefinition.points).all()
    earned = {sb.badge_id: sb for sb in db.query(StudentBadge).filter(StudentBadge.eleve_id == current_user.id).all()}

    result = []
    for b in all_badges:
        result.append({
            "id": b.id,
            "nom": b.nom,
            "description": b.description,
            "icon_url": b.icon_url,
            "couleur": b.couleur,
            "categorie": b.categorie,
            "points": b.points,
            "obtenu": b.id in earned,
            "date_obtention": earned[b.id].date_obtention.isoformat() if b.id in earned else None,
        })
    return result


@router.post("/badges/check")
def trigger_badge_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Vérifie et décerne les badges éligibles."""
    new_badges = check_and_award_badges(current_user.id, db)
    return {"new_badges": new_badges, "count": len(new_badges)}


@router.get("/streak")
def get_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne le streak actuel et les 30 derniers jours."""
    current = get_current_streak(current_user.id, db)

    streaks = db.query(StudentStreak).filter(
        StudentStreak.eleve_id == current_user.id,
    ).order_by(StudentStreak.date_jour.desc()).limit(30).all()

    total_points = sum(s.points_jour for s in streaks)

    return {
        "current_streak": current,
        "total_points": total_points,
        "history": [
            {
                "date": s.date_jour.isoformat(),
                "login": s.streak_login,
                "quiz": s.streak_quiz,
                "objectif": s.streak_objectif,
                "points": s.points_jour,
            }
            for s in streaks
        ],
    }


@router.post("/streak/record")
def record_activity(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enregistre une activité quotidienne."""
    streak = record_daily_streak(
        current_user.id, db,
        login=body.get("login", False),
        quiz=body.get("quiz", False),
        objectif=body.get("objectif", False),
    )
    check_and_award_badges(current_user.id, db)
    return {"message": "Activité enregistrée", "points_jour": streak.points_jour}


@router.get("/rankings")
def get_rankings(
    matiere_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Classement du palier de l'élève."""
    palier = get_student_tier(current_user, db)

    compute_rankings(matiere_id, palier, db)

    rankings = db.query(StudentRanking).filter(
        StudentRanking.palier == palier,
    )
    if matiere_id:
        rankings = rankings.filter(StudentRanking.matiere_id == matiere_id)
    rankings = rankings.order_by(StudentRanking.rang).limit(50).all()

    my_rank = None
    for r in rankings:
        if r.eleve_id == current_user.id:
            my_rank = {"rang": r.rang, "points": r.points_total}
            break

    return {
        "palier": palier,
        "rankings": [
            {"rang": r.rang, "eleve_id": r.eleve_id, "points": r.points_total}
            for r in rankings
        ],
        "me": my_rank,
    }
