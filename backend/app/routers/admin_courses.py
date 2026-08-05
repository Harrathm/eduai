"""
Course builder API backed by the existing Course/Module/Lesson tables.
"""

import json
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from sqlalchemy import text, func
from app.deps import require_admin, get_user_role, require_active_subscription
from app.services.course_lifecycle import can_transition_status
from app.audit import log_admin_action

from app.models import Course, CourseStatus, Module, Lesson, User, UserRole

router = APIRouter(tags=["Admin Courses"])


# ---- Pydantic Schemas ----

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = None
    cover_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = Field(default="beginner")
    price_tokens: Optional[int] = Field(default=0, ge=0)
    price_dt: Optional[float] = Field(default=0.0, ge=0)
    max_students: Optional[int] = None
    language: Optional[str] = "fr"
    prerequisites: Optional[str] = None
    learning_objectives: Optional[str] = None
    visibility: Optional[str] = "public"
    enrollment_type: Optional[str] = "open"
    tags: Optional[list[str]] = None

    model_config = ConfigDict(extra="allow")


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = None
    cover_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    price_tokens: Optional[int] = Field(None, ge=0)
    price_dt: Optional[float] = Field(None, ge=0)
    max_students: Optional[int] = None
    language: Optional[str] = None
    prerequisites: Optional[str] = None
    learning_objectives: Optional[str] = None
    visibility: Optional[str] = None
    enrollment_type: Optional[str] = None
    tags: Optional[list[str]] = None

    model_config = ConfigDict(extra="allow")


class ChapterCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order: Optional[int] = 0


class ChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order: Optional[int] = None

    model_config = ConfigDict(extra="allow")


# ---- Helpers ----

def _status_value(course: Course) -> str:
    if course.status is None:
        return "draft"
    return course.status.value if hasattr(course.status, "value") else str(course.status)


def _slugify(title: str, course_id: int) -> str:
    base = re.sub(r'[^a-z0-9]+', '-', title.lower().strip())
    return f"{base}-{course_id}"


def _validate_publish(course: Course, db: Session) -> list[str]:
    errors = []
    if not course.title or not course.title.strip():
        errors.append("Le titre est obligatoire")
    if not course.short_description and not course.description:
        errors.append("La description courte ou la description est obligatoire")
    modules_count = db.query(Module).filter(Module.course_id == course.id).count()
    if modules_count == 0:
        errors.append("Le cours doit avoir au moins un chapitre")
    lessons_count = db.execute(
        text("SELECT COUNT(*) FROM lessons l JOIN modules m ON m.id = l.module_id WHERE m.course_id = :course_id"),
        {"course_id": course.id},
    ).scalar() or 0
    if lessons_count == 0:
        errors.append("Le cours doit avoir au moins une leçon")
    return errors


def _serialize_lesson(row: dict) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row.get("description"),
        "lesson_type": row.get("lesson_type") or "text",
        "content_text": row.get("content_text"),
        "content_url": row.get("content_url"),
        "video_url": row.get("video_url"),
        "pdf_url": row.get("pdf_url"),
        "image_urls": json.loads(row["image_urls"]) if row.get("image_urls") else [],
        "link_url": row.get("link_url"),
        "link_title": row.get("link_title"),
        "order": row.get("order") or 0,
        "duration_minutes": row.get("duration_minutes") or 0,
        "is_free": bool(row.get("is_free")),
        "created_at": str(row.get("created_at", "")),
    }


def _serialize_chapter(db: Session, module: Module, include_lessons: bool = True) -> dict:
    data = {
        "id": module.id,
        "title": module.title,
        "description": module.description,
        "order": module.order or 0,
        "order_index": module.order or 0,
    }
    if include_lessons:
        rows = db.execute(
            text("""
                SELECT id, module_id, title, description, lesson_type, content_text,
                       content_url, video_url, pdf_url, image_urls, link_url, link_title,
                       "order", duration_minutes, is_free, created_at
                FROM lessons WHERE module_id = :module_id ORDER BY "order"
            """),
            {"module_id": module.id},
        ).mappings()
        data["lessons"] = [_serialize_lesson(dict(row)) for row in rows]
    return data


def _serialize_course(db: Session, course: Course, include_chapters: bool = False) -> dict:
    modules = sorted(course.modules, key=lambda m: m.order or 0) if course.modules else []
    lessons_count = db.execute(
        text("""
            SELECT COUNT(*) FROM lessons l
            JOIN modules m ON m.id = l.module_id
            WHERE m.course_id = :course_id
        """),
        {"course_id": course.id},
    ).scalar() or 0
    students_enrolled = db.execute(
        text("SELECT COUNT(*) FROM course_purchases WHERE course_id = :course_id"),
        {"course_id": course.id},
    ).scalar() or 0
    author_name = course.author.full_name if course.author else "Unknown"

    modifier_name = None
    if course.modified_by:
        modifier = db.query(User).filter(User.id == course.modified_by).first()
        modifier_name = modifier.full_name if modifier else None

    data = {
        "id": course.id,
        "uuid": str(course.uuid) if course.uuid else None,
        "title": course.title,
        "description": course.description,
        "short_description": course.short_description,
        "cover_url": course.thumbnail_url or course.cover_url,
        "thumbnail_url": course.thumbnail_url or course.cover_url,
        "category": course.category,
        "level": course.level or "beginner",
        "status": _status_value(course),
        "price_tokens": course.price_tokens or 0,
        "price_dt": course.price_dt or 0.0,
        "is_free": not bool(course.price_tokens or course.price_dt),
        "total_chapters": len(modules),
        "total_modules": len(modules),
        "total_lessons": lessons_count,
        "teacher_id": course.author_id,
        "teacher_name": author_name,
        "author_name": author_name,
        "modified_by": course.modified_by,
        "modifier_name": modifier_name,
        "max_students": course.max_students,
        "students_enrolled": students_enrolled,
        "is_published": bool(course.is_published),
        "published_at": course.published_at.isoformat() if course.published_at else None,
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "updated_at": course.updated_at.isoformat() if course.updated_at else None,
        "language": course.language or "fr",
        "prerequisites": course.prerequisites,
        "learning_objectives": course.learning_objectives,
        "visibility": course.visibility or "public",
        "enrollment_type": course.enrollment_type or "open",
        "tags": course.tags or [],
    }
    if include_chapters:
        data["chapters"] = [_serialize_chapter(db, module) for module in modules]
    return data


def _can_access_course(admin: User, course: Course) -> bool:
    role = get_user_role(admin)
    if role == "super_admin":
        return True
    return course.school_id == admin.school_id


# ---- Routes ----

@router.get("")
def list_courses(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    role = get_user_role(admin)
    query = db.query(Course)

    if role != "super_admin":
        query = query.filter(Course.school_id == admin.school_id)

    if status_filter:
        query = query.filter(Course.status == status_filter)
    if search:
        query = query.filter(
            (Course.title.ilike(f"%{search}%")) | (Course.description.ilike(f"%{search}%"))
        )
    if category:
        query = query.filter(Course.category == category)
    if level:
        query = query.filter(Course.level == level)

    total = query.count()
    courses = query.order_by(Course.updated_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [_serialize_course(db, course) for course in courses]}


@router.get("/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied to this school")
    return _serialize_course(db, course, include_chapters=True)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin), _sub=Depends(require_active_subscription)):
    if not admin.school_id:
        raise HTTPException(status_code=400, detail="Aucun établissement associé à votre compte")

    course = Course(
        school_id=admin.school_id,
        author_id=admin.id,
        title=data.title,
        description=data.description,
        short_description=data.short_description,
        thumbnail_url=data.cover_url or data.thumbnail_url,
        category=data.category,
        level=data.level or "beginner",
        price_tokens=data.price_tokens or 0,
        price_dt=data.price_dt or 0.0,
        max_students=data.max_students,
        language=data.language or "fr",
        prerequisites=data.prerequisites,
        learning_objectives=data.learning_objectives,
        visibility=data.visibility or "public",
        enrollment_type=data.enrollment_type or "open",
        tags=json.dumps(data.tags) if data.tags else None,
        status=CourseStatus.DRAFT,
        is_published=False,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    course.slug = _slugify(course.title, course.id)
    db.commit()
    log_admin_action("course.create", admin.id, admin_email=admin.email, target_type="course", target_id=course.id, details={"title": course.title}, db=db)
    return _serialize_course(db, course)


@router.patch("/{course_id}")
def update_course(course_id: int, data: CourseUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    if "cover_url" in update_data:
        update_data["thumbnail_url"] = update_data.pop("cover_url")
    if "tags" in update_data:
        update_data["tags"] = json.dumps(update_data["tags"])

    for field, value in update_data.items():
        if hasattr(course, field):
            setattr(course, field, value)

    course.updated_at = datetime.now(timezone.utc)
    course.modified_by = admin.id
    db.commit()
    db.refresh(course)
    log_admin_action("course.update", admin.id, admin_email=admin.email, target_type="course", target_id=course.id, db=db)
    return _serialize_course(db, course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")
    db.delete(course)
    db.commit()
    log_admin_action("course.delete", admin.id, admin_email=admin.email, target_type="course", target_id=course_id, db=db)


@router.post("/{course_id}/publish")
def publish_course(
    course_id: int,
    price_tokens: int = Query(0, ge=0),
    price_dt: float = Query(0.0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    errors = _validate_publish(course, db)
    if errors:
        raise HTTPException(status_code=422, detail={"message": "Publication impossible", "errors": errors})

    course.status = CourseStatus.PUBLISHED
    course.is_published = True
    course.price_tokens = price_tokens
    course.price_dt = price_dt
    course.published_at = datetime.now(timezone.utc)
    course.modified_by = admin.id
    course.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(course)
    return _serialize_course(db, course)


@router.post("/{course_id}/submit-for-review")
def submit_for_review(course_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Soumet un cours pour review pédagogique (draft → pending_review)."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    can_transition_status(course, "pending_review", admin)

    course.pedagogical_status = "pending_review"
    course.modified_by = admin.id
    course.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(course)
    return {"id": course.id, "pedagogical_status": course.pedagogical_status}


@router.post("/{course_id}/unpublish")
def unpublish_course(course_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")
    course.status = CourseStatus.DRAFT
    course.is_published = False
    course.published_at = None
    course.modified_by = admin.id
    course.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(course)
    return _serialize_course(db, course)


@router.post("/{course_id}/archive")
def archive_course(course_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")
    course.status = CourseStatus.ARCHIVED
    course.is_published = False
    course.published_at = None
    course.modified_by = admin.id
    course.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(course)
    return _serialize_course(db, course)


@router.post("/{course_id}/duplicate")
def duplicate_course(course_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    original = db.query(Course).filter(Course.id == course_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, original):
        raise HTTPException(status_code=403, detail="Access denied")

    new_course = Course(
        school_id=original.school_id,
        author_id=admin.id,
        title=f"{original.title} (Copie)",
        description=original.description,
        short_description=original.short_description,
        thumbnail_url=original.thumbnail_url,
        cover_url=getattr(original, 'cover_url', None),
        category=original.category,
        level=original.level,
        price_tokens=original.price_tokens,
        price_dt=original.price_dt,
        max_students=original.max_students,
        language=original.language,
        prerequisites=original.prerequisites,
        learning_objectives=original.learning_objectives,
        visibility=original.visibility,
        enrollment_type=original.enrollment_type,
        tags=original.tags,
        status=CourseStatus.DRAFT,
        is_published=False,
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    new_course.slug = _slugify(new_course.title, new_course.id)

    for module in original.modules:
        new_module = Module(
            course_id=new_course.id,
            title=module.title,
            description=module.description,
            order=module.order,
        )
        db.add(new_module)
        db.commit()
        db.refresh(new_module)

        for lesson in module.lessons:
            new_lesson = Lesson(
                module_id=new_module.id,
                school_id=new_course.school_id,
                teacher_id=admin.id,
                title=lesson.title,
                description=lesson.description,
                lesson_type=lesson.lesson_type,
                content_type=lesson.content_type,
                content_text=lesson.content_text,
                content_url=lesson.content_url,
                video_url=lesson.video_url,
                pdf_url=lesson.pdf_url,
                image_urls=lesson.image_urls,
                link_url=lesson.link_url,
                link_title=lesson.link_title,
                order=lesson.order,
                duration_minutes=lesson.duration_minutes,
                is_free=lesson.is_free,
                is_preview=lesson.is_preview,
            )
            db.add(new_lesson)

    db.commit()
    return _serialize_course(db, new_course, include_chapters=True)


@router.post("/{course_id}/reorder")
def reorder_chapters(
    course_id: int,
    body: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    order = body.get("order", [])
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    for idx, module_id in enumerate(order):
        module = db.query(Module).filter(Module.id == module_id, Module.course_id == course_id).first()
        if module:
            module.order = idx

    course.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "order": order}


@router.get("/{course_id}/preview")
def preview_course(course_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Admin preview of any course (draft/published) with full chapter/lesson tree."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order).all()
    modules_data = []
    for module in modules:
        lessons = db.query(Lesson).filter(Lesson.module_id == module.id).order_by(Lesson.order).all()
        lessons_data = []
        for l in lessons:
            lessons_data.append({
                "id": l.id,
                "title": l.title or "",
                "description": l.description or "",
                "lesson_type": l.lesson_type or "text",
                "content_text": l.content_text,
                "video_url": l.video_url,
                "pdf_url": l.pdf_url,
                "image_urls": json.loads(l.image_urls) if l.image_urls else [],
                "link_url": l.link_url,
                "link_title": l.link_title,
                "duration_minutes": l.duration_minutes or 0,
                "is_free": bool(l.is_free),
                "is_preview": bool(l.is_preview),
            })
        modules_data.append({
            "id": module.id,
            "title": module.title or "",
            "description": module.description or "",
            "order": module.order or 0,
            "lessons": lessons_data,
        })

    return {
        "id": course.id,
        "title": course.title or "",
        "short_description": course.short_description or "",
        "description": course.description or "",
        "cover_url": course.thumbnail_url or course.cover_url,
        "thumbnail_url": course.thumbnail_url,
        "category": course.category,
        "level": course.level or "beginner",
        "language": course.language or "fr",
        "tags": course.tags or [],
        "prerequisites": course.prerequisites or "",
        "learning_objectives": course.learning_objectives or "",
        "price_tokens": course.price_tokens or 0,
        "price_dt": float(course.price_dt or 0),
        "visibility": course.visibility or "public",
        "enrollment_type": course.enrollment_type or "open",
        "status": _status_value(course),
        "is_published": bool(course.is_published),
        "total_modules": len(modules_data),
        "total_lessons": sum(len(m["lessons"]) for m in modules_data),
        "total_duration_minutes": course.total_duration_minutes or 0,
        "modules": modules_data,
        "author_name": course.author.full_name if course.author else "Unknown",
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "published_at": course.published_at.isoformat() if course.published_at else None,
    }


@router.get("/{course_id}/analytics")
def course_analytics(course_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    total_students = db.execute(
        text("SELECT COUNT(*) FROM course_purchases WHERE course_id = :course_id"),
        {"course_id": course_id}
    ).scalar() or 0

    total_lessons = db.execute(
        text("""
            SELECT COUNT(*) FROM lessons l
            JOIN modules m ON m.id = l.module_id
            WHERE m.course_id = :course_id
        """),
        {"course_id": course_id}
    ).scalar() or 0

    total_chapters = db.query(Module).filter(Module.course_id == course_id).count()

    completed_lessons = db.execute(
        text("""
            SELECT COUNT(DISTINCT lp.lesson_id)
            FROM lesson_progress lp
            JOIN lessons l ON l.id = lp.lesson_id
            JOIN modules m ON m.id = l.module_id
            WHERE m.course_id = :course_id AND lp.completed = true
        """),
        {"course_id": course_id}
    ).scalar() or 0

    completion_rate = round((completed_lessons / max(total_lessons, 1)) * 100, 1)

    return {
        "course_id": course_id,
        "total_students": total_students,
        "total_chapters": total_chapters,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "completion_rate": completion_rate,
    }


# ---- Chapter Management (nested under course) ----

@router.get("/{course_id}/chapters")
def list_chapters(course_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order).all()
    return [_serialize_chapter(db, module) for module in modules]


@router.post("/{course_id}/chapters")
def create_chapter(course_id: int, data: ChapterCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    max_order = db.query(Module).filter(Module.course_id == course_id).count()

    module = Module(
        course_id=course_id,
        title=data.title,
        description=data.description,
        order=data.order if data.order is not None else max_order,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    course.updated_at = datetime.now(timezone.utc)
    course.modified_by = admin.id
    db.commit()
    return _serialize_chapter(db, module)


@router.get("/{course_id}/chapters/{chapter_id}")
def get_chapter(course_id: int, chapter_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    module = db.query(Module).filter(Module.id == chapter_id, Module.course_id == course_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return _serialize_chapter(db, module)


@router.patch("/{course_id}/chapters/{chapter_id}")
def update_chapter(course_id: int, chapter_id: int, data: ChapterUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    module = db.query(Module).filter(Module.id == chapter_id, Module.course_id == course_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Chapter not found")

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if hasattr(module, field):
            setattr(module, field, value)

    db.commit()
    db.refresh(module)
    return _serialize_chapter(db, module)


@router.delete("/{course_id}/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(course_id: int, chapter_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _can_access_course(admin, course):
        raise HTTPException(status_code=403, detail="Access denied")

    module = db.query(Module).filter(Module.id == chapter_id, Module.course_id == course_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Chapter not found")

    db.delete(module)
    course.updated_at = datetime.now(timezone.utc)
    course.modified_by = admin.id
    db.commit()


# ============================================================
# B2B ACADEMY DISTRIBUTION (Super Admin only)
# ============================================================

def _require_super_admin(current_user: User = Depends(get_current_user)):
    role = get_user_role(current_user)
    if role != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return current_user


class GrantCourseRequest(BaseModel):
    course_id: int
    price_paid_dt: float = 0.0
    is_active: bool = True


@router.get("/schools/course-access")
def list_school_course_access(
    db: Session = Depends(get_db),
    admin: User = Depends(_require_super_admin),
):
    """Super Admin: see all schools and which courses they have access to."""
    from app.models import School, SchoolCourseAccess, User as UserModel

    result = []
    schools = db.query(School).order_by(School.name).all()

    for school in schools:
        accesses = db.query(SchoolCourseAccess).filter(
            SchoolCourseAccess.school_id == school.id
        ).all()

        course_ids = [a.course_id for a in accesses]
        courses_map = {}
        if course_ids:
            for c in db.query(Course).filter(Course.id.in_(course_ids)).all():
                courses_map[c.id] = c

        granted = []
        for a in accesses:
            course = courses_map.get(a.course_id)
            if not course:
                continue
            enrolled_count = db.query(UserModel).join(
                SchoolCourseAccess,
                SchoolCourseAccess.course_id == course.id,
            ).filter(
                UserModel.school_id == school.id,
                UserModel.role.in_([UserRole.STUDENT, UserRole.TEACHER]),
                SchoolCourseAccess.is_active == True,
            ).count()

            granted.append({
                "course_id": course.id,
                "course_title": course.title,
                "course_slug": course.slug,
                "course_category": course.category,
                "course_level": course.level,
                "purchased_at": a.purchased_at.isoformat() if a.purchased_at else None,
                "is_active": a.is_active,
                "price_paid_dt": a.price_paid_dt,
                "granted_by_admin_id": a.granted_by,
                "enrolled_users_count": enrolled_count,
            })

        user_counts = db.query(UserModel.role, func.count(UserModel.id)).filter(
            UserModel.school_id == school.id,
        ).group_by(UserModel.role).all()
        counts = {r: c for r, c in user_counts}

        result.append({
            "school_id": school.id,
            "school_name": school.name,
            "school_slug": school.slug,
            "total_users": sum(counts.values()),
            "student_count": counts.get(UserRole.STUDENT, 0),
            "teacher_count": counts.get(UserRole.TEACHER, 0),
            "granted_courses": granted,
        })

    return {
        "total_schools": len(result),
        "academy_courses_count": db.query(Course).filter(Course.is_published == True).count(),
        "schools": result,
    }


@router.get("/schools/course-access/available-courses")
def list_available_academy_courses(
    db: Session = Depends(get_db),
    admin: User = Depends(_require_super_admin),
):
    """List all published academy courses available for granting."""
    courses = db.query(Course).filter(
        Course.is_published == True,
    ).order_by(Course.title).all()
    return {
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "slug": c.slug,
                "category": c.category,
                "level": c.level,
                "price_dt": c.price_dt,
                "price_tokens": c.price_tokens,
                "total_modules": c.total_modules,
                "total_lessons": c.total_lessons,
            }
            for c in courses
        ],
    }


@router.post("/schools/{school_id}/grant-course")
def grant_course_to_school(
    school_id: int,
    body: GrantCourseRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(_require_super_admin),
):
    """Super Admin: grant/assign a course to a school."""
    from app.models import School, SchoolCourseAccess

    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    course = db.query(Course).filter(Course.id == body.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # RESTRICTION B2B: le cours doit être approved_for_b2b ET owner_typeschool ou eduai_catalog
    if course.pedagogical_status != "approved_for_b2b":
        raise HTTPException(
            status_code=400,
            detail=f"Le cours '{course.title}' n'est pas approuvé pour la distribution B2B (statut actuel: {course.pedagogical_status})"
        )
    if course.owner_type == "independent_teacher":
        raise HTTPException(
            status_code=400,
            detail=f"Le cours '{course.title}' appartient à un enseignant indépendant et ne peut pas être distribué en B2B"
        )

    existing = db.query(SchoolCourseAccess).filter(
        SchoolCourseAccess.school_id == school_id,
        SchoolCourseAccess.course_id == body.course_id,
    ).first()

    if existing:
        existing.is_active = body.is_active
        if body.price_paid_dt:
            existing.price_paid_dt = body.price_paid_dt
        db.commit()
        db.refresh(existing)
        return {"ok": True, "action": "updated", "access_id": existing.id}

    access = SchoolCourseAccess(
        school_id=school_id,
        course_id=body.course_id,
        is_active=body.is_active,
        price_paid_dt=body.price_paid_dt,
        granted_by=admin.id,
    )
    db.add(access)
    db.commit()
    db.refresh(access)

    # Audit log
    try:
        from app.routers.admin import audit_log
        audit_log(db, admin.id, admin.email, "course.grant",
                  target_type="school_course_access", target_id=access.id,
                  details=f"Granted course #{body.course_id} to school #{school_id}")
    except Exception:
        pass

    return {"ok": True, "action": "granted", "access_id": access.id}


@router.delete("/schools/{school_id}/revoke-course/{course_id}")
def revoke_course_from_school(
    school_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(_require_super_admin),
):
    """Super Admin: revoke a course from a school."""
    from app.models import SchoolCourseAccess

    access = db.query(SchoolCourseAccess).filter(
        SchoolCourseAccess.school_id == school_id,
        SchoolCourseAccess.course_id == course_id,
    ).first()
    if not access:
        raise HTTPException(status_code=404, detail="Access record not found")

    access.is_active = False
    db.commit()

    try:
        from app.routers.admin import audit_log
        audit_log(db, admin.id, admin.email, "course.revoke",
                  target_type="school_course_access", target_id=access.id,
                  details=f"Revoked course #{course_id} from school #{school_id}")
    except Exception:
        pass

    return {"ok": True, "action": "revoked"}
