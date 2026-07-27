"""
Learner API - Course viewer, progress tracking, quiz taking, certificates
"""

import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.auth import get_current_user
from app.deps import require_super_admin
from app.models import User, UserRole, VerificationStatus
from app.models import (
    Course, Module, Lesson, CourseEnrollment, Certificate,
    Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer,
    Note, Bookmark, LessonProgress, CourseOwnerType
)
from app.services.course_access import has_course_access

router = APIRouter(tags=["Learner"])


def require_authenticated(current_user: User = Depends(get_current_user)):
    return current_user


# ============ Preview for Super Admin ============

@router.get("/courses/{course_id}/preview", response_model=dict)
def preview_course(
    course_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin)
):
    """Preview any course (draft or published) exactly as learners will see it"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Preview requested for course_id={course_id} by user={user.id}")
    
    try:
        from app.models import Course, Module, Lesson
        
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        logger.info(f"Course found: {course.title}")
        
        # Get modules safely
        modules = db.query(Module).filter(Module.course_id == course_id).all()
        logger.info(f"Modules found: {len(modules)}")
        
        modules_data = []
        for module in modules:
            lessons = db.query(Lesson).filter(Lesson.module_id == module.id).order_by(Lesson.order).all()
            lessons_data = []
            for l in lessons:
                quiz_data = None
                if l.quiz_id:
                    quiz = db.query(Quiz).filter(Quiz.id == l.quiz_id).first()
                    if quiz:
                        quiz_data = {
                            "id": quiz.id,
                            "title": quiz.title,
                            "description": quiz.description,
                            "time_limit_seconds": quiz.time_limit_seconds,
                            "passing_score_percent": quiz.passing_score_percent
                        }
                lessons_data.append({
                    "id": l.id,
                    "title": l.title or "Untitled",
                    "description": l.description or "",
                    "lesson_type": l.lesson_type or "text",
                    "content_html": l.content_html,
                    "content_text": l.content_text,
                    "content_url": l.content_url,
                    "video_url": l.video_url,
                    "video_duration_seconds": l.video_duration_seconds,
                    "video_thumbnail_url": l.video_thumbnail_url,
                    "pdf_url": l.pdf_url,
                    "document_url": l.document_url,
                    "document_type": l.document_type,
                    "image_urls": l.image_urls,
                    "link_url": l.link_url,
                    "link_title": l.link_title,
                    "duration_minutes": l.duration_minutes or 0,
                    "is_free": bool(l.is_free),
                    "is_preview": bool(l.is_preview),
                    "quiz": quiz_data,
                    "course_title": course.title,
                    "module_title": module.title
                })
            modules_data.append({
                "id": module.id,
                "title": module.title or "Untitled",
                "description": module.description or "",
                "order": module.order or 0,
                "cover_url": module.cover_url,
                "lessons": lessons_data
            })
        
        # Get status safely
        course_status = "draft"
        if course.status:
            if hasattr(course.status, 'value'):
                course_status = course.status.value
            else:
                course_status = str(course.status)
        
        result = {
            "id": course.id,
            "title": course.title or "",
            "short_description": course.short_description or "",
            "description": course.description or "",
            "cover_url": course.cover_url,
            "thumbnail_url": course.thumbnail_url,
            "category": course.category,
            "level": course.level or "beginner",
            "language": course.language or "fr",
            "tags": course.tags,
            "prerequisites": course.prerequisites or "",
            "learning_objectives": course.learning_objectives or "",
            "price_tokens": course.price_tokens or 0,
            "price_dt": float(course.price_dt or 0),
            "is_free": (course.price_tokens or 0) == 0 and float(course.price_dt or 0) == 0,
            "total_modules": len(modules_data),
            "total_lessons": sum(len(m["lessons"]) for m in modules_data),
            "total_duration_minutes": course.total_duration_minutes or 0,
            "status": course_status,
            "is_preview": True,
            "modules": modules_data,
            "author_id": course.author_id,
            "created_at": course.created_at.isoformat() if course.created_at else None,
            "published_at": course.published_at.isoformat() if course.published_at else None
        }
        logger.info(f"Preview ready for course {course_id}")
        return result
        
    except Exception as e:
        logger.error(f"Preview error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")


# ============ Catalog (Public) ============

@router.get("/courses")
def list_published_courses(
    skip: int = 0,
    limit: int = 20,
    category: str = None,
    level: str = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    """Public course catalog - shows only published courses"""
    from app.models import Course, CourseStatus
    query = db.query(Course).filter(Course.is_published == True)
    
    if category:
        query = query.filter(Course.category == category)
    if level:
        query = query.filter(Course.level == level)
    if search:
        query = query.filter(Course.title.ilike(f"%{search}%"))
    
    total = query.count()
    courses = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": c.id,
                "title": c.title,
                "short_description": c.short_description or "",
                "description": c.description,
                "cover_url": c.cover_url,
                "thumbnail_url": c.thumbnail_url,
                "category": c.category,
                "level": c.level or "beginner",
                "tags": c.tags,
                "price_tokens": c.price_tokens or 0,
                "price_dt": float(c.price_dt or 0),
                "is_free": (c.price_tokens or 0) == 0 and float(c.price_dt or 0) == 0,
                "total_modules": c.total_modules or 0,
                "total_lessons": c.total_lessons or 0,
                "total_duration_minutes": c.total_duration_minutes or 0,
                "author_id": c.author_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in courses
        ],
    }


@router.get("/catalog")
def list_catalog(
    skip: int = 0,
    limit: int = 20,
    category: str = None,
    niveau_scolaire: str = None,
    search: str = None,
    db: Session = Depends(get_db),
):
    """Platform catalog — eduai_catalog courses only (formations pour enseignants/élèves)."""
    query = db.query(Course).filter(
        Course.is_published == True,
        Course.owner_type == CourseOwnerType.EDUAI_CATALOG.value,
    )

    if category:
        query = query.filter(Course.category == category)
    if niveau_scolaire:
        query = query.filter(Course.niveau_scolaire == niveau_scolaire)
    if search:
        query = query.filter(Course.title.ilike(f"%{search}%"))

    total = query.count()
    courses = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "title": c.title,
                "short_description": c.short_description or "",
                "description": c.description,
                "cover_url": c.cover_url,
                "thumbnail_url": c.thumbnail_url,
                "category": c.category,
                "level": c.level or "beginner",
                "niveau_scolaire": c.niveau_scolaire,
                "tags": c.tags,
                "price_tokens": c.price_tokens or 0,
                "price_dt": float(c.price_dt or 0),
                "is_free": (c.price_tokens or 0) == 0 and float(c.price_dt or 0) == 0,
                "total_modules": c.total_modules or 0,
                "total_lessons": c.total_lessons or 0,
                "total_duration_minutes": c.total_duration_minutes or 0,
                "author_id": c.author_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in courses
        ],
    }


@router.get("/courses/{course_id}", response_model=dict)
def get_course_detail(course_id: int, db: Session = Depends(get_db)):
    """Get published course details"""
    from app.models import Course, CourseStatus
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.is_published == True,
        Course.visibility != "school_only"
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {
        "id": course.id,
        "title": course.title,
        "short_description": course.short_description or "",
        "description": course.description,
        "cover_url": course.cover_url,
        "thumbnail_url": course.thumbnail_url,
        "category": course.category,
        "level": course.level or "beginner",
        "language": course.language or "fr",
        "tags": course.tags,
        "prerequisites": course.prerequisites or "",
        "learning_objectives": course.learning_objectives or "",
        "price_tokens": course.price_tokens or 0,
        "price_dt": float(course.price_dt or 0),
        "is_free": (course.price_tokens or 0) == 0 and float(course.price_dt or 0) == 0,
        "total_modules": course.total_modules or 0,
        "total_lessons": course.total_lessons or 0,
        "total_duration_minutes": course.total_duration_minutes or 0,
        "visibility": course.visibility or "public",
        "enrollment_type": course.enrollment_type or "open",
        "author_id": course.author_id,
        "created_at": course.created_at.isoformat() if course.created_at else None,
    }


@router.get("/courses/{course_id}/syllabus", response_model=List[dict])
def get_course_syllabus(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_authenticated)):
    from app.deps import get_user_role
    is_super = get_user_role(current_user) == "super_admin"

    course_query = db.query(Course).filter(Course.id == course_id)
    if not is_super:
        course_query = course_query.filter(Course.is_published == True)
    course = course_query.first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if not is_super and not has_course_access(current_user, course, db):
        raise HTTPException(
            status_code=403,
            detail="Accès non autorisé — achetez ce cours ou le pack correspondant"
        )

    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order).all()
    result = []
    for module in modules:
        lessons = db.query(Lesson).filter(Lesson.module_id == module.id).order_by(Lesson.order).all()
        result.append({
            "id": module.id,
            "title": module.title,
            "description": module.description,
            "order_index": module.order or 0,
            "lessons": [
                {
                    "id": l.id,
                    "title": l.title,
                    "lesson_type": l.lesson_type or "text",
                    "duration_minutes": l.duration_minutes or 0,
                    "is_free": bool(l.is_free),
                    "status": "not_started",
                    "has_quiz": l.quiz_id is not None
                }
                for l in lessons
            ]
        })
    return result


# ============ Enrollment ============

@router.post("/courses/{course_id}/enroll", response_model=dict)
def enroll_in_course(
    course_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.is_published == True
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id,
        CourseEnrollment.course_id == course_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled")

    enrollment = CourseEnrollment(
        student_id=user.id,
        course_id=course_id,
        status="active"
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    # Check if placement test should be recommended
    from app.services.student_tier import get_student_tier
    tier = get_student_tier(user, db)
    placement_test_available = False
    placement_test_id = None
    if tier in ("excellence", "etablissement"):
        test = db.query(PlacementTest).filter(
            PlacementTest.matiere == course.matiere if hasattr(course, 'matiere') else True,
            PlacementTest.is_active == True
        ).first()
        if test:
            existing_result = db.query(PlacementTestResult).filter(
                PlacementTestResult.user_id == user.id,
                PlacementTestResult.placement_test_id == test.id
            ).first()
            if not existing_result:
                placement_test_available = True
                placement_test_id = test.id
    
    return {
        "id": enrollment.id,
        "status": enrollment.status,
        "placement_test_available": placement_test_available,
        "placement_test_id": placement_test_id
    }


@router.get("/my-courses")
def my_enrolled_courses(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    query = db.query(CourseEnrollment).filter(CourseEnrollment.student_id == user.id)
    total = query.count()
    enrollments = query.offset(skip).limit(limit).all()
    result = []
    for e in enrollments:
        course = db.query(Course).filter(Course.id == e.course_id).first()
        if course:
            result.append({
                "enrollment_id": e.id,
                "course_id": course.id,
                "title": course.title,
                "thumbnail_url": course.thumbnail_url,
                "cover_url": course.cover_url,
                "progress_percent": e.progress_percent,
                "status": e.status
            })
    return {"total": total, "skip": skip, "limit": limit, "items": result}


# ============ Lesson Progress ============

@router.get("/lessons/{lesson_id}", response_model=dict)
def get_lesson_content(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    from app.deps import get_user_role
    is_super = get_user_role(user) == "super_admin"

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    course = db.query(Course).filter(Course.id == module.course_id).first()

    if not is_super:
        # Free lessons are always accessible; paid lessons require course access
        if not lesson.is_free and not has_course_access(user, course, db):
            raise HTTPException(
                status_code=403,
                detail="Accès non autorisé — achetez ce cours ou le pack correspondant"
            )

    quiz_data = None
    if lesson.quiz_id:
        quiz = db.query(Quiz).filter(Quiz.id == lesson.quiz_id).first()
        if quiz:
            quiz_data = {
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "time_limit_seconds": quiz.time_limit_seconds,
                "passing_score_percent": quiz.passing_score_percent
            }

    return {
        "id": lesson.id,
        "title": lesson.title,
        "description": lesson.description,
        "lesson_type": lesson.lesson_type or "text",
        "content_html": lesson.content_html,
        "content_text": lesson.content_text,
        "content_url": lesson.content_url,
        "video_url": lesson.video_url,
        "video_duration_seconds": lesson.video_duration_seconds,
        "video_thumbnail_url": lesson.video_thumbnail_url,
        "pdf_url": lesson.pdf_url,
        "document_url": lesson.document_url,
        "document_type": lesson.document_type,
        "image_urls": lesson.image_urls,
        "link_url": lesson.link_url,
        "link_title": lesson.link_title,
        "duration_minutes": lesson.duration_minutes or 0,
        "quiz": quiz_data,
        "course_title": course.title,
        "module_title": module.title if module else None
    }


@router.post("/lessons/{lesson_id}/progress")
def update_lesson_progress(
    lesson_id: int,
    progress_data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    from datetime import datetime as dt, timezone

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    course = db.query(Course).filter(Course.id == module.course_id).first()

    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id,
        CourseEnrollment.course_id == course.id
    ).first()
    if not enrollment:
        enrollment = CourseEnrollment(
            student_id=user.id,
            course_id=course.id,
            status="active",
            progress_percent=0,
        )
        db.add(enrollment)
        db.flush()

    progress = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id == enrollment.id,
        LessonProgress.lesson_id == lesson_id
    ).first()

    if not progress:
        progress = LessonProgress(
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
            status="in_progress",
            started_at=dt.now(timezone.utc)
        )
        db.add(progress)

    status_val = progress_data.get("status", "in_progress")
    progress.status = status_val

    if "video_position_seconds" in progress_data:
        progress.video_position_seconds = progress_data["video_position_seconds"]
    if "video_completed" in progress_data:
        progress.video_completed = progress_data["video_completed"]
    if "content_completed" in progress_data:
        progress.content_completed = progress_data["content_completed"]
    if "quiz_completed" in progress_data:
        progress.quiz_completed = progress_data["quiz_completed"]
    if "quiz_passed" in progress_data:
        progress.quiz_passed = progress_data["quiz_passed"]
    if "quiz_score" in progress_data:
        progress.quiz_score = progress_data["quiz_score"]

    if status_val == "completed":
        progress.completed_at = dt.now(timezone.utc)

    db.commit()

    total_lessons = db.query(Lesson).filter(Lesson.module_id.in_(
        db.query(Module.id).filter(Module.course_id == course.id)
    )).count()
    completed_lessons = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id == enrollment.id,
        LessonProgress.status == "completed"
    ).count()

    progress_percent = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0
    enrollment.progress_percent = progress_percent

    if progress_percent >= 100:
        enrollment.status = "completed"
        enrollment.completed_at = dt.now(timezone.utc)

        existing_cert = db.query(Certificate).filter(
            Certificate.student_id == user.id,
            Certificate.course_id == course.id
        ).first()

        if not existing_cert:
            import secrets
            cert = Certificate(
                student_id=user.id,
                course_id=course.id,
                enrollment_id=enrollment.id,
                certificate_number=f"CERT-{secrets.randbelow(1000000):06d}",
                student_name=user.full_name or user.email,
                course_name=course.title,
                verification_code=secrets.token_hex(16)
            )
            db.add(cert)

    db.commit()
    return {"success": True, "progress_percent": progress_percent}


# ============ Quiz Taking ============

@router.post("/quizzes/{quiz_id}/start")
def start_quiz_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    """Start a new quiz attempt"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Check course access via the lesson's parent course
    from app.deps import get_user_role
    is_super = get_user_role(user) == "super_admin"
    if not is_super:
        lesson = db.query(Lesson).filter(Lesson.quiz_id == quiz_id).first()
        if lesson:
            module = db.query(Module).filter(Module.id == lesson.module_id).first()
            course = db.query(Course).filter(Course.id == module.course_id).first()
            if not has_course_access(user, course, db):
                raise HTTPException(
                    status_code=403,
                    detail="Accès non autorisé — achetez ce cours ou le pack correspondant"
                )

    if quiz.max_attempts:
        existing = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.student_id == user.id,
            QuizAttempt.status == "completed"
        ).count()
        if existing >= quiz.max_attempts:
            raise HTTPException(status_code=400, detail="Maximum attempts reached")

    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=user.id,
        status="in_progress"
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {"attempt_id": attempt.id}


@router.get("/quizzes/{quiz_id}")
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    """Get quiz questions for player"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Check course access
    from app.deps import get_user_role
    is_super = get_user_role(user) == "super_admin"
    if not is_super:
        lesson = db.query(Lesson).filter(Lesson.quiz_id == quiz_id).first()
        if lesson:
            module = db.query(Module).filter(Module.id == lesson.module_id).first()
            course = db.query(Course).filter(Course.id == module.course_id).first()
            if not has_course_access(user, course, db):
                raise HTTPException(
                    status_code=403,
                    detail="Accès non autorisé — achetez ce cours ou le pack correspondant"
                )

    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.order_index).all()
    return {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "time_limit_seconds": quiz.time_limit_seconds,
        "passing_score_percent": quiz.passing_score_percent,
        "questions": [
            {
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "points": q.points,
                "options": [
                    {"id": o.id, "text": o.option_text}
                    for o in db.query(QuizOption).filter(QuizOption.question_id == q.id).order_by(QuizOption.order_index).all()
                ]
            }
            for q in questions
        ]
    }


@router.post("/quizzes/{quiz_id}/submit")
def submit_quiz_attempt(
    quiz_id: int,
    attempt_data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    """Submit quiz attempt by quiz_id (legacy)"""
    attempt_id = attempt_data.get("attempt_id")
    if not attempt_id:
        raise HTTPException(status_code=400, detail="attempt_id required")
    return _do_submit_attempt(attempt_id, attempt_data.get("answers", []), db, user)


@router.post("/quiz-attempts/{attempt_id}/submit")
def submit_quiz_by_attempt(
    attempt_id: int,
    attempt_data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    """Submit quiz by attempt ID"""
    return _do_submit_attempt(attempt_id, attempt_data.get("answers", []), db, user)


def _do_submit_attempt(attempt_id: int, answers: list, db: Session, user: User) -> dict:
    """Common submit logic"""
    from datetime import datetime as dt, timezone

    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.id == attempt_id,
        QuizAttempt.student_id == user.id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.status != "in_progress":
        raise HTTPException(status_code=400, detail="Attempt already submitted")

    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
    correct_count = 0
    total_points = 0
    earned_points = 0
    total_count = 0

    for answer in answers:
        question_id = answer.get("question_id")
        selected_ids = answer.get("selected_option_ids", [])
        text_answer = answer.get("text_answer")

        question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
        if not question:
            continue

        total_count += 1
        total_points += question.points

        import json as json_mod
        sa = QuizAnswer(
            attempt_id=attempt.id,
            question_id=question_id,
            selected_option_ids=json_mod.dumps(selected_ids) if selected_ids else None,
            text_answer=text_answer
        )
        db.add(sa)

        if question.question_type in ["mcq", "multi", "truefalse"]:
            correct_options = db.query(QuizOption).filter(
                QuizOption.question_id == question_id,
                QuizOption.is_correct == True
            ).all()
            correct_ids = {o.id for o in correct_options}
            sel_set = set(selected_ids or [])

            if question.question_type == "mcq":
                is_correct = len(sel_set) == 1 and sel_set == correct_ids
            else:
                is_correct = sel_set == correct_ids

            sa.is_correct = is_correct
            sa.points_awarded = question.points if is_correct else 0
            if is_correct:
                correct_count += 1
            earned_points += sa.points_awarded
        else:
            sa.points_awarded = 0

    attempted_questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == attempt.quiz_id).count()
    attempt.total_count = attempted_questions
    attempt.correct_count = correct_count
    attempt.score = earned_points
    attempt.score_percent = round((earned_points / total_points * 100), 2) if total_points > 0 else 0
    attempt.passed = attempt.score_percent >= quiz.passing_score_percent
    attempt.status = "completed"
    attempt.completed_at = dt.now(timezone.utc)
    attempt.graded_at = dt.now(timezone.utc)

    db.commit()

    return {
        "attempt_id": attempt.id,
        "score": attempt.score,
        "score_percent": attempt.score_percent,
        "correct_count": correct_count,
        "total_count": total_count,
        "passed": attempt.passed
    }


# ============ Certificates ============

@router.get("/certificates")
def my_certificates(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    query = db.query(Certificate).filter(Certificate.student_id == user.id)
    total = query.count()
    certs = query.offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": [
        {
            "id": c.id,
            "certificate_number": c.certificate_number,
            "course_name": c.course_name,
            "student_name": c.student_name,
            "issue_date": c.issue_date,
            "status": c.status,
            "pdf_url": c.pdf_url,
            "verification_code": c.verification_code
        }
        for c in certs
    ]}


@router.get("/certificates/{cert_id}", response_model=dict)
def get_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    cert = db.query(Certificate).filter(
        Certificate.id == cert_id,
        Certificate.student_id == user.id
    ).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return {
        "id": cert.id,
        "certificate_number": cert.certificate_number,
        "student_name": cert.student_name,
        "course_name": cert.course_name,
        "issue_date": cert.issue_date,
        "expiry_date": cert.expiry_date,
        "status": cert.status,
        "pdf_url": cert.pdf_url,
        "verification_code": cert.verification_code
    }


@router.get("/courses/{course_id}/certificate")
def get_course_certificate(
    course_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == user.id,
        CourseEnrollment.course_id == course_id
    ).first()

    if not enrollment or enrollment.status != "completed":
        raise HTTPException(status_code=404, detail="Not eligible for certificate")

    cert = db.query(Certificate).filter(
        Certificate.student_id == user.id,
        Certificate.course_id == course_id
    ).first()

    if not cert:
        import secrets
        course = db.query(Course).filter(Course.id == course_id).first()
        cert = Certificate(
            student_id=user.id,
            course_id=course_id,
            enrollment_id=enrollment.id,
            certificate_number=f"CERT-{secrets.randbelow(1000000):06d}",
            student_name=user.full_name or user.email,
            course_name=course.title if course else "Course",
            verification_code=secrets.token_hex(16)
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)

    return {
        "id": cert.id,
        "certificate_number": cert.certificate_number,
        "course_name": cert.course_name,
        "student_name": cert.student_name,
        "issue_date": cert.issue_date,
        "verification_code": cert.verification_code,
        "pdf_url": cert.pdf_url
    }


# ============ Notes ============

@router.post("/lessons/{lesson_id}/notes")
def add_note(
    lesson_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    note = Note(
        user_id=user.id,
        lesson_id=lesson_id,
        content=data.get("content", ""),
        position=data.get("position")
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "created_at": note.created_at}


@router.get("/lessons/{lesson_id}/notes")
def get_notes(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    notes = db.query(Note).filter(
        Note.user_id == user.id,
        Note.lesson_id == lesson_id
    ).order_by(Note.created_at.desc()).all()
    return [
        {"id": n.id, "content": n.content, "position": n.position, "created_at": n.created_at}
        for n in notes
    ]


# ============ Bookmarks ============

@router.post("/lessons/{lesson_id}/bookmarks")
def add_bookmark(
    lesson_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    bookmark = Bookmark(
        user_id=user.id,
        lesson_id=lesson_id,
        position_seconds=data.get("position_seconds", 0),
        note=data.get("note")
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return {"id": bookmark.id}


@router.get("/lessons/{lesson_id}/bookmarks")
def get_bookmarks(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated)
):
    bookmarks = db.query(Bookmark).filter(
        Bookmark.user_id == user.id,
        Bookmark.lesson_id == lesson_id
    ).order_by(Bookmark.position_seconds).all()
    return [
        {"id": b.id, "position_seconds": b.position_seconds, "note": b.note, "created_at": b.created_at}
        for b in bookmarks
    ]


# ============================================================
# IDENTITY VERIFICATION (non-blocking, independent teachers)
# ============================================================

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "verifications")


@router.post("/verify-identity")
async def upload_verification_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a justificatif (diploma, CIN) for identity verification.

    Only independent_paid teachers are concerned.  This never blocks
    normal usage — it only gates future visibility in the public catalog.
    """
    if current_user.subscription_plan != "independent_paid":
        raise HTTPException(status_code=400, detail="Verification is only available for independent paid accounts")

    allowed = {"application/pdf", "image/jpeg", "image/png"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=415, detail="Only PDF, JPEG, PNG accepted")

    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB)")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "doc")[1] or ".pdf"
    filename = f"verify_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    current_user.verification_document_url = filename
    current_user.verification_status = VerificationStatus.PENDING
    db.commit()

    return {"ok": True, "status": "pending", "message": "Document submitted for review"}


@router.get("/verify-identity/status")
def get_verification_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current verification status of the user."""
    return {
        "status": current_user.verification_status,
        "document_url": current_user.verification_document_url,
        "reviewed_at": current_user.verification_reviewed_at.isoformat() if current_user.verification_reviewed_at else None,
        "rejection_reason": current_user.verification_rejection_reason,
    }


# ============================================================
# SUBSCRIPTION STATUS
# ============================================================

@router.get("/subscription/status")
def get_my_subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return subscription status and expiration info."""
    from app.tasks.subscription_expiration import get_subscription_status
    return get_subscription_status(current_user)


# ============================================================
# TIER RECOMMENDATIONS
# ============================================================

from app.services.recommendation import get_recommended_path, get_daily_objective
from app.services.student_tier import get_student_tier
from app.services.course_access import has_course_access


# ============================================================
# TIER-DIFFERENTIATED DASHBOARD
# ============================================================

@router.get("/dashboard")
def learner_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tableau de bord différencié selon le palier de l'élève.
    - Découverte  : progression simple, objectif quotidien, accès de base
    - Excellence  : analytics détaillés, objectifs ciblés, recommandations IA
    - Établissement : parcours complet, analytics école, objectifs programme
    """
    tier = get_student_tier(current_user, db)
    today = datetime.now(timezone.utc).date()

    # Données communes
    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id
    ).all()

    courses = []
    total_progress = 0.0
    total_lessons_completed = 0
    total_lessons = 0

    for e in enrollments:
        course = db.query(Course).filter(Course.id == e.course_id).first()
        if not course or course.status != "published":
            continue

        course_lessons = db.query(Lesson).join(Module).filter(
            Module.course_id == course.id
        ).count()
        completed = db.query(LessonProgress).filter(
            LessonProgress.enrollment_id == e.id,
            LessonProgress.status == "completed",
        ).count()

        progress = round((completed / course_lessons) * 100, 1) if course_lessons > 0 else 0.0
        total_lessons_completed += completed
        total_lessons += course_lessons

        course_data = {
            "id": course.id,
            "title": course.title,
            "niveau_scolaire": course.niveau_scolaire,
            "progress_pct": progress,
            "lessons_completed": completed,
            "total_lessons": course_lessons,
        }

        # Excellence/etablissement : ajouter la matière pour analytics
        if tier in ("excellence", "etablissement"):
            course_data["matiere"] = course.matiere or ""

        courses.append(course_data)

    total_progress = round((total_lessons_completed / total_lessons) * 100, 1) if total_lessons > 0 else 0.0

    # Objectif quotidien
    daily = get_daily_objective(current_user, db)

    # Dashboard selon palier
    dashboard = {
        "tier": tier,
        "user_id": current_user.id,
        "total_enrolled_courses": len(enrollments),
        "overall_progress_pct": total_progress,
        "lessons_completed": total_lessons_completed,
        "total_lessons": total_lessons,
        "courses": courses,
        "daily_objective": daily,
    }

    if tier == "decouverte":
        dashboard["features"] = {
            "ai_access": "questions simples (ask/explain)",
            "placement_test": False,
            "recommendations": "parcours guidé",
            "analytics": False,
        }
        dashboard["encouragement"] = _get_encouragement_message(total_progress)

    elif tier == "excellence":
        dashboard["features"] = {
            "ai_access": "exercices ciblés + questions",
            "placement_test": True,
            "recommendations": "adaptatives",
            "analytics": True,
        }
        # Ajouter les stats matière
        dashboard["matiere_stats"] = _get_matiere_stats(courses)

    else:  # etablissement
        dashboard["features"] = {
            "ai_access": "tout (contenu personnalisé)",
            "placement_test": True,
            "recommendations": "programme national",
            "analytics": True,
            "school_content": True,
        }
        dashboard["matiere_stats"] = _get_matiere_stats(courses)
        # Cours de l'école disponibles
        if current_user.school_id:
            school_courses = db.query(Course).filter(
                Course.school_id == current_user.school_id,
                Course.status == "published",
                ~Course.id.in_([e.course_id for e in enrollments]),
            ).limit(5).all()
            dashboard["suggested_school_courses"] = [
                {"id": c.id, "title": c.title, "niveau_scolaire": c.niveau_scolaire}
                for c in school_courses
            ]

    return dashboard


def _get_encouragement_message(progress_pct: float) -> str:
    """Retourne un message d'encouragement pour le palier découverte."""
    if progress_pct < 25:
        return "Bien démarré ! Continuez comme ça"
    elif progress_pct < 50:
        return "Vous avancez bien !"
    elif progress_pct < 75:
        return "Excellent progrès !"
    else:
        return "Formidable ! Vous maîtrisez presque tout"


def _get_matiere_stats(courses: list) -> dict:
    """Calcule les stats par matière pour excellence/etablissement."""
    stats = {}
    for c in courses:
        matiere = c.get("matiere", "général")
        if matiere not in stats:
            stats[matiere] = {"total": 0, "completed": 0, "progress_pct": 0.0}
        stats[matiere]["total"] += c.get("total_lessons", 0)
        stats[matiere]["completed"] += c.get("lessons_completed", 0)

    for m in stats.values():
        if m["total"] > 0:
            m["progress_pct"] = round((m["completed"] / m["total"]) * 100, 1)

    return stats


@router.get("/recommended-path")
def recommended_learning_path(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne le parcours d'apprentissage recommandé selon le palier de l'élève."""
    return get_recommended_path(current_user, db)


@router.get("/daily-objective")
def daily_objective(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne l'objectif quotidien de l'élève selon son palier."""
    return get_daily_objective(current_user, db)