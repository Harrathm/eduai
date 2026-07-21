"""
Service de recommandations et parcours personnalisés selon les paliers d'élèves.
- Découverte  : parcours guidé avec objectifs quotidiens
- Excellence  : recommandations adaptatives basées sur les performances
- Établissement : parcours aligné au programme national + contenu école
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    User, Course, Lesson, Module,
    LessonProgress, CourseEnrollment,
    PackPurchase, PlacementTestResult,
)
from app.services.student_tier import get_student_tier


def utcnow():
    return datetime.now(timezone.utc)


def get_recommended_path(user: User, db: Session) -> dict:
    tier = get_student_tier(user, db)
    if tier == "decouverte":
        return _get_guided_path(user, db)
    elif tier == "excellence":
        return _get_adaptive_path(user, db)
    else:
        return _get_curriculum_path(user, db)


def get_daily_objective(user: User, db: Session) -> dict:
    tier = get_student_tier(user, db)
    today = utcnow().date()
    if tier == "decouverte":
        return _get_discovery_objective(user, db, today)
    elif tier == "excellence":
        return _get_excellence_objective(user, db, today)
    else:
        return _get_establissement_objective(user, db, today)


# ──────────────────────────────────────────────────────────
# DÉCOUVERTE
# ──────────────────────────────────────────────────────────

def _get_guided_path(user: User, db: Session) -> dict:
    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id
    ).all()

    courses = []
    for e in enrollments:
        course = db.query(Course).filter(Course.id == e.course_id).first()
        if course and course.status == "published":
            progress = _get_course_progress(user, course, db)
            courses.append({
                "id": course.id,
                "title": course.title,
                "niveau_scolaire": course.niveau_scolaire,
                "progress_pct": progress,
                "priority": "guided",
            })

    courses.sort(key=lambda c: c["progress_pct"])

    return {
        "tier": "decouverte",
        "description": "Parcours guidé — objectifs quotidiens simples",
        "courses": courses[:5],
        "next_step": "Complétez au moins 1 leçon aujourd'hui pour maintenir votre progression",
    }


def _get_discovery_objective(user: User, db: Session, today) -> dict:
    enrollment_ids = [e.id for e in db.query(CourseEnrollment.id).filter(
        CourseEnrollment.student_id == user.id
    ).all()]

    if not enrollment_ids:
        return {
            "tier": "decouverte",
            "type": "no_enrollment",
            "message": "Inscrivez-vous à un cours pour commencer votre parcours guidé",
            "estimated_minutes": 0,
        }

    last_progress = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id.in_(enrollment_ids),
        LessonProgress.status == "completed",
    ).order_by(LessonProgress.completed_at.desc()).first()

    if last_progress:
        lesson = db.query(Lesson).filter(Lesson.id == last_progress.lesson_id).first()
        if lesson:
            next_lesson = db.query(Lesson).filter(
                Lesson.module_id == lesson.module_id,
                Lesson.order > lesson.order,
            ).order_by(Lesson.order.asc()).first()
            if next_lesson:
                return {
                    "tier": "decouverte",
                    "type": "continue_lesson",
                    "lesson_id": next_lesson.id,
                    "lesson_title": next_lesson.title,
                    "module_title": lesson.module.title if lesson.module else "",
                    "message": f"Continuez avec « {next_lesson.title} » aujourd'hui",
                    "estimated_minutes": 15,
                }

    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id
    ).first()
    if enrollment:
        course = db.query(Course).filter(Course.id == enrollment.course_id).first()
        if course:
            first_lesson = db.query(Lesson).join(Module).filter(
                Module.course_id == course.id
            ).order_by(Module.order, Lesson.order).first()
            if first_lesson:
                return {
                    "tier": "decouverte",
                    "type": "start_course",
                    "lesson_id": first_lesson.id,
                    "lesson_title": first_lesson.title,
                    "course_title": course.title,
                    "message": f"Commencez « {course.title} » avec la leçon « {first_lesson.title} »",
                    "estimated_minutes": 15,
                }

    return {
        "tier": "decouverte",
        "type": "no_lessons",
        "message": "Aucune leçon disponible — contactez votre administrateur",
        "estimated_minutes": 0,
    }


# ──────────────────────────────────────────────────────────
# EXCELLENCE
# ──────────────────────────────────────────────────────────

def _get_adaptive_path(user: User, db: Session) -> dict:
    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id
    ).all()

    courses = []
    for e in enrollments:
        course = db.query(Course).filter(Course.id == e.course_id).first()
        if course and course.status == "published":
            progress = _get_course_progress(user, course, db)
            matiere = course.matiere or course.title
            courses.append({
                "id": course.id,
                "title": course.title,
                "niveau_scolaire": course.niveau_scolaire,
                "matiere": matiere,
                "progress_pct": progress,
                "priority": "adaptive",
                "action": "review" if progress < 50 else "practice",
            })

    matieres = {}
    for c in courses:
        m = c.get("matiere", "général")
        if m not in matieres:
            matieres[m] = []
        matieres[m].append(c["progress_pct"])

    weakest_matiere = min(matieres.items(), key=lambda x: sum(x[1]) / len(x[1]))[0] if matieres else None

    return {
        "tier": "excellence",
        "description": "Parcours adaptatif — recommandations personnalisées",
        "courses": courses[:7],
        "weakest_subject": weakest_matiere,
        "next_step": f"Travaillez sur {weakest_matiere} pour améliorer votre moyenne" if weakest_matiere else "Continuez votre progression",
    }


def _get_excellence_objective(user: User, db: Session, today) -> dict:
    enrollment_ids = [e.id for e in db.query(CourseEnrollment.id).filter(
        CourseEnrollment.student_id == user.id
    ).all()]

    if not enrollment_ids:
        return {
            "tier": "excellence",
            "type": "no_enrollment",
            "message": "Inscrivez-vous à un cours pour recevoir des exercices ciblés",
            "estimated_minutes": 0,
        }

    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id
    ).all()

    for e in enrollments:
        course = db.query(Course).filter(Course.id == e.course_id).first()
        if not course or course.status != "published":
            continue

        progress = _get_course_progress(user, course, db)
        if progress < 70:
            completed_lesson_ids = [lp.lesson_id for lp in db.query(LessonProgress.lesson_id).filter(
                LessonProgress.enrollment_id == e.id,
                LessonProgress.status == "completed",
            ).all()]

            unfinished = db.query(Lesson).join(Module).filter(
                Module.course_id == course.id,
                ~Lesson.id.in_(completed_lesson_ids) if completed_lesson_ids else True,
            ).order_by(Module.order, Lesson.order).first()

            if unfinished:
                return {
                    "tier": "excellence",
                    "type": "adaptive_practice",
                    "lesson_id": unfinished.id,
                    "lesson_title": unfinished.title,
                    "course_title": course.title,
                    "message": f"Exercices ciblés : complétez « {unfinished.title} » pour renforcer {course.matiere or course.title}",
                    "estimated_minutes": 20,
                }

    return {
        "tier": "excellence",
        "type": "review",
        "message": "Révision recommandée — relisez vos leçons récentes",
        "estimated_minutes": 10,
    }


# ──────────────────────────────────────────────────────────
# ÉTABLISSEMENT
# ──────────────────────────────────────────────────────────

def _get_curriculum_path(user: User, db: Session) -> dict:
    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id
    ).all()

    courses = []
    for e in enrollments:
        course = db.query(Course).filter(Course.id == e.course_id).first()
        if course and course.status == "published":
            progress = _get_course_progress(user, course, db)
            courses.append({
                "id": course.id,
                "title": course.title,
                "niveau_scolaire": course.niveau_scolaire,
                "matiere": course.matiere or "",
                "progress_pct": progress,
                "priority": "curriculum",
                "aligned": True,
            })

    return {
        "tier": "etablissement",
        "description": "Parcours programme national — contenu aligné au curriculum",
        "courses": courses,
        "next_step": "Suivez le programme de votre établissement",
    }


def _get_establissement_objective(user: User, db: Session, today) -> dict:
    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id
    ).all()

    for e in enrollments:
        course = db.query(Course).filter(Course.id == e.course_id).first()
        if not course or course.status != "published":
            continue

        completed_lesson_ids = [lp.lesson_id for lp in db.query(LessonProgress.lesson_id).filter(
            LessonProgress.enrollment_id == e.id,
            LessonProgress.status == "completed",
        ).all()]

        unfinished = db.query(Lesson).join(Module).filter(
            Module.course_id == course.id,
            ~Lesson.id.in_(completed_lesson_ids) if completed_lesson_ids else True,
        ).order_by(Module.order, Lesson.order).first()

        if unfinished:
            return {
                "tier": "etablissement",
                "type": "curriculum_lesson",
                "lesson_id": unfinished.id,
                "lesson_title": unfinished.title,
                "course_title": course.title,
                "message": f"Programme établissement : « {unfinished.title} » ({course.matiere or course.title})",
                "estimated_minutes": 25,
            }

    return {
        "tier": "etablissement",
        "type": "no_pending",
        "message": "Toutes les leçons du programme sont complétées — bravo !",
        "estimated_minutes": 0,
    }


# ──────────────────────────────────────────────────────────
# UTILITAIRES
# ──────────────────────────────────────────────────────────

def _get_course_progress(user: User, course: Course, db: Session) -> float:
    total_lessons = db.query(Lesson).join(Module).filter(
        Module.course_id == course.id
    ).count()
    if total_lessons == 0:
        return 0.0

    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id,
        CourseEnrollment.course_id == course.id,
    ).first()
    if not enrollment:
        return 0.0

    completed_lessons = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id == enrollment.id,
        LessonProgress.status == "completed",
    ).count()

    return round((completed_lessons / total_lessons) * 100, 1)
