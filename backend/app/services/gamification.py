"""Gamification — badges, streaks, classements."""

from datetime import date, timedelta, datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    BadgeDefinition, StudentBadge, StudentStreak, StudentRanking,
    User, HistoriqueScoreEleve, ProfilAssimilationEleve, ChapterPathway, Matiere,
)
from app.services.student_tier import get_student_tier


def check_and_award_badges(user_id: int, db: Session) -> list[str]:
    """Vérifie les critères et décerne les badges éligibles. Retourne les noms des badges gagnés."""
    badges_gagnes = []
    existing = {sb.badge_id for sb in db.query(StudentBadge).filter(StudentBadge.eleve_id == user_id).all()}
    all_badges = db.query(BadgeDefinition).all()

    for badge in all_badges:
        if badge.id in existing:
            continue
        if _check_criteria(user_id, badge, db):
            db.add(StudentBadge(eleve_id=user_id, badge_id=badge.id))
            db.commit()
            badges_gagnes.append(badge.nom)

    return badges_gagnes


def _check_criteria(user_id: int, badge: BadgeDefinition, db: Session) -> bool:
    if badge.critere_type == "quiz_count":
        count = db.query(HistoriqueScoreEleve).filter(HistoriqueScoreEleve.eleve_id == user_id).count()
        return count >= badge.critere_valeur
    elif badge.critere_type == "score_avg":
        result = db.query(func.avg(HistoriqueScoreEleve.score)).filter(
            HistoriqueScoreEleve.eleve_id == user_id
        ).scalar()
        return (result or 0) >= (badge.critere_valeur / 100)
    elif badge.critere_type == "streak_days":
        streak = db.query(StudentStreak).filter(
            StudentStreak.eleve_id == user_id,
            StudentStreak.streak_login == True,
        ).order_by(StudentStreak.date_jour.desc()).limit(badge.critere_valeur).all()
        if len(streak) < badge.critere_valeur:
            return False
        for i in range(len(streak) - 1):
            diff = (streak[i].date_jour - streak[i + 1].date_jour).days
            if diff != 1:
                return False
        return True
    elif badge.critere_type == "chapters_completed":
        count = db.query(ProfilAssimilationEleve).filter(
            ProfilAssimilationEleve.eleve_id == user_id,
            ProfilAssimilationEleve.statut_validation == "valide_enseignant",
        ).count()
        return count >= badge.critere_valeur
    return False


def record_daily_streak(user_id: int, db: Session, login: bool = False, quiz: bool = False, objectif: bool = False):
    """Enregistre l'activité quotidienne d'un élève."""
    today = date.today()
    streak = db.query(StudentStreak).filter(
        StudentStreak.eleve_id == user_id,
        StudentStreak.date_jour == today,
    ).first()

    if not streak:
        streak = StudentStreak(
            eleve_id=user_id,
            date_jour=today,
            streak_login=login,
            streak_quiz=quiz,
            streak_objectif=objectif,
            points_jour=(3 if login else 0) + (5 if quiz else 0) + (10 if objectif else 0),
        )
        db.add(streak)
    else:
        if login:
            streak.streak_login = True
        if quiz:
            streak.streak_quiz = True
        if objectif:
            streak.streak_objectif = True
        streak.points_jour = (3 if streak.streak_login else 0) + (5 if streak.streak_quiz else 0) + (10 if streak.streak_objectif else 0)
    db.commit()
    return streak


def get_current_streak(user_id: int, db: Session) -> int:
    """Retourne le nombre de jours consécutifs avec streak_login."""
    streaks = db.query(StudentStreak).filter(
        StudentStreak.eleve_id == user_id,
        StudentStreak.streak_login == True,
    ).order_by(StudentStreak.date_jour.desc()).all()

    if not streaks:
        return 0

    today = date.today()
    if streaks[0].date_jour != today and streaks[0].date_jour != today - timedelta(days=1):
        return 0

    count = 1
    for i in range(len(streaks) - 1):
        diff = (streaks[i].date_jour - streaks[i + 1].date_jour).days
        if diff == 1:
            count += 1
        else:
            break
    return count


def compute_rankings(matiere_id: Optional[int], palier: str, db: Session):
    """Recalcule les classements pour un palier et optionnellement une matière."""
    from app.services.student_tier import get_student_tier

    students = db.query(User).filter(User.role == "student").all()
    rankings = []
    for student in students:
        student_tier = get_student_tier(student, db)
        if student_tier != palier:
            continue

        query = db.query(func.sum(StudentStreak.points_jour)).filter(
            StudentStreak.eleve_id == student.id,
        )
        total_points = query.scalar() or 0

        rankings.append({
            "eleve_id": student.id,
            "eleve_nom": student.full_name,
            "points": total_points,
        })

    rankings.sort(key=lambda x: x["points"], reverse=True)

    now = datetime.now(timezone.utc)
    for i, r in enumerate(rankings):
        existing = db.query(StudentRanking).filter(
            StudentRanking.eleve_id == r["eleve_id"],
            StudentRanking.palier == palier,
            StudentRanking.matiere_id == matiere_id,
        ).first()
        if existing:
            existing.points_total = r["points"]
            existing.rang = i + 1
            existing.date_calcul = now
        else:
            db.add(StudentRanking(
                eleve_id=r["eleve_id"],
                matiere_id=matiere_id,
                palier=palier,
                points_total=r["points"],
                rang=i + 1,
                date_calcul=now,
            ))
    db.commit()
    return rankings
