"""
Catalog API - Public course browsing (/catalog prefix)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.models import Course, CourseStatus, Module, Lesson, User, UserRole

router = APIRouter()


@router.get("/courses")
def list_courses(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    language: Optional[str] = None,
    price: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Public course catalog - shows only published courses with visibility='public_catalog'"""
    query = db.query(Course).filter(
        Course.status == CourseStatus.PUBLISHED,
        Course.visibility == "public_catalog",
    )

    if search:
        query = query.filter(Course.title.ilike(f"%{search}%"))
    if category:
        query = query.filter(Course.category == category)
    if level:
        query = query.filter(Course.level == level)
    if language:
        query = query.filter(Course.language == language)
    if price == "free":
        query = query.filter((Course.price_tokens == 0) & (Course.price_dt == 0))
    elif price == "paid":
        query = query.filter((Course.price_tokens > 0) | (Course.price_dt > 0))

    total = query.count()
    courses = query.order_by(Course.published_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "title": c.title,
                "slug": c.slug,
                "description": (c.short_description or c.description or "")[:200],
                "cover_url": c.cover_url,
                "category": c.category,
                "level": c.level,
                "language": c.language,
                "is_free": (c.price_tokens or 0) == 0 and float(c.price_dt or 0) == 0,
                "price_tokens": c.price_tokens or 0,
                "price_dt": float(c.price_dt or 0),
                "total_modules": c.total_modules or 0,
                "total_lessons": c.total_lessons or 0,
                "total_duration_minutes": c.total_duration_minutes or 0,
            }
            for c in courses
        ]
    }


@router.get("/courses/{slug}")
def get_course_detail(slug: str, db: Session = Depends(get_db)):
    """Get published course detail by slug"""
    course = db.query(Course).filter(
        Course.slug == slug,
        Course.status == CourseStatus.PUBLISHED,
        Course.visibility != "school_only"
    ).first()

    if not course:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Course not found")

    modules = db.query(Module).filter(Module.course_id == course.id).order_by(Module.order).all()
    chapters = []
    for mod in modules:
        lessons_q = db.query(Lesson).filter(Lesson.module_id == mod.id).order_by(Lesson.order).all()
        lessons = [
            {
                "id": l.id,
                "title": l.title,
                "lesson_type": l.lesson_type or "text",
                "duration_minutes": l.duration_minutes or 0,
                "is_free": l.is_free or False
            }
            for l in lessons_q
        ]
        chapters.append({
            "id": mod.id,
            "title": mod.title,
            "order_index": mod.order,
            "lessons": lessons
        })

    return {
        "id": course.id,
        "title": course.title,
        "slug": course.slug,
        "description": course.description,
        "cover_url": course.cover_url,
        "category": course.category,
        "level": course.level,
        "language": course.language,
        "is_free": (course.price_tokens or 0) == 0 and float(course.price_dt or 0) == 0,
        "price_tokens": course.price_tokens or 0,
        "price_dt": float(course.price_dt or 0),
        "total_modules": course.total_modules or 0,
        "total_lessons": course.total_lessons or 0,
        "estimated_duration_minutes": course.total_duration_minutes or 0,
        "chapters": chapters
    }


@router.get("/stats")
def platform_stats(db: Session = Depends(get_db)):
    """Public platform stats: teacher count, course count."""
    teacher_count = db.query(User).filter(
        User.role == UserRole.TEACHER,
        User.is_active == True,
    ).count()
    course_count = db.query(Course).filter(
        Course.status == CourseStatus.PUBLISHED,
    ).count()
    return {
        "teachers": teacher_count,
        "courses": course_count,
    }


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """List all categories from published courses"""
    cats = db.query(Course.category).filter(
        Course.status == CourseStatus.PUBLISHED,
        Course.category.isnot(None)
    ).distinct().all()
    return [c[0] for c in cats if c[0]]