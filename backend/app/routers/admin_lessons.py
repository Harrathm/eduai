"""Lesson API backed by the existing lessons table."""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.deps import require_admin, require_course_writer, get_user_role, require_active_subscription
from app.audit import log_admin_action
from app.models import Course, Module, Lesson, User


router = APIRouter(tags=["Admin Lessons"])


def _can_access_module(db: Session, user: User, module: Module) -> None:
    role = get_user_role(user)
    if role == "super_admin":
        return
    if role == "pedagogical_admin":
        return
    course = db.query(Course).filter(Course.id == module.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if role == "teacher":
        if course.author_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        return
    if course.school_id != user.school_id:
        raise HTTPException(status_code=403, detail="Access denied")


class LessonCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    lesson_type: str = Field(default="text")
    content_text: str | None = None
    content_url: str | None = None
    video_url: str | None = None
    pdf_url: str | None = None
    document_url: str | None = None
    document_type: str | None = None
    image_urls: list[str] | None = None
    link_url: str | None = None
    link_title: str | None = None
    order: int | None = None
    duration_minutes: int = Field(default=0, ge=0)
    is_free: bool = False
    quiz_id: int | None = None


class LessonUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    module_id: int | None = None
    lesson_type: str | None = None
    content_text: str | None = None
    content_url: str | None = None
    video_url: str | None = None
    pdf_url: str | None = None
    document_url: str | None = None
    document_type: str | None = None
    image_urls: list[str] | None = None
    link_url: str | None = None
    link_title: str | None = None
    order: int | None = None
    duration_minutes: int | None = None
    is_free: bool | None = None
    quiz_id: int | None = None

    model_config = ConfigDict(extra="allow")


def _serialize_lesson(lesson: Lesson) -> dict:
    return {
        "id": lesson.id,
        "chapter_id": lesson.module_id,
        "title": lesson.title,
        "description": lesson.description,
        "lesson_type": lesson.lesson_type or "text",
        "content_type": lesson.content_type.value if hasattr(lesson.content_type, 'value') else (lesson.content_type or "text"),
        "content_text": lesson.content_text,
        "content_url": lesson.content_url,
        "video_url": lesson.video_url,
        "pdf_url": lesson.pdf_url,
        "document_url": lesson.document_url,
        "document_type": lesson.document_type,
        "image_urls": json.loads(lesson.image_urls) if lesson.image_urls else [],
        "link_url": lesson.link_url,
        "link_title": lesson.link_title,
        "order": lesson.order or 0,
        "duration_minutes": lesson.duration_minutes or 0,
        "is_free": bool(lesson.is_free),
        "is_preview": bool(lesson.is_preview) if lesson.is_preview is not None else False,
        "quiz_id": lesson.quiz_id,
        "ai_generated": bool(lesson.ai_generated) if lesson.ai_generated is not None else False,
        "tokens_used": lesson.tokens_used,
        "created_at": str(lesson.created_at) if lesson.created_at else None,
        "updated_at": str(lesson.updated_at) if lesson.updated_at else None,
    }


@router.get("")
def list_lessons(
    module_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    category_cible: Optional[str] = None,
    niveau_scolaire: Optional[str] = None,
    matiere: Optional[str] = None,
    chapitre_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_course_writer),
):
    query = db.query(Lesson).join(Module, Lesson.module_id == Module.id).join(Course, Module.course_id == Course.id)

    if module_id is not None:
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Chapter not found")
        _can_access_module(db, admin, module)
        query = query.filter(Lesson.module_id == module_id)
    else:
        role = get_user_role(admin)
        if role not in ("super_admin", "pedagogical_admin") and admin.school_id:
            query = query.filter(
                (Lesson.school_id == admin.school_id) | (Course.is_published == True)
            )

    if chapitre_id is not None:
        query = query.filter(Lesson.module_id == chapitre_id)
    if category_cible:
        query = query.filter(Course.category_cible == category_cible)
    if niveau_scolaire:
        query = query.filter(Course.niveau_scolaire == niveau_scolaire)
    if matiere:
        query = query.filter(Course.category == matiere)
    if search:
        query = query.filter(Lesson.title.ilike(f"%{search}%"))

    total = query.count()
    lessons = query.order_by(Lesson.order).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": [_serialize_lesson(l) for l in lessons]}


@router.get("/{lesson_id}")
def get_lesson(lesson_id: int, db: Session = Depends(get_db), admin: User = Depends(require_course_writer)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    if module:
        _can_access_module(db, admin, module)
    return _serialize_lesson(lesson)


@router.post("", status_code=201)
def create_lesson(
    module_id: int,
    data: LessonCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_course_writer),
    _sub=Depends(require_active_subscription),
):
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Chapter not found")
    _can_access_module(db, admin, module)

    course = db.query(Course).filter(Course.id == module.course_id).first()

    max_order = db.query(Lesson).filter(Lesson.module_id == module_id).count()

    lesson = Lesson(
        module_id=module_id,
        school_id=course.school_id if course else (admin.school_id or 1),
        teacher_id=admin.id,
        title=data.title,
        description=data.description,
        lesson_type=data.lesson_type,
        content_text=data.content_text,
        content_url=data.content_url,
        video_url=data.video_url,
        pdf_url=data.pdf_url,
        document_url=data.document_url,
        document_type=data.document_type,
        image_urls=json.dumps(data.image_urls) if data.image_urls else None,
        link_url=data.link_url,
        link_title=data.link_title,
        order=data.order if data.order is not None else max_order,
        duration_minutes=data.duration_minutes,
        is_free=data.is_free,
        quiz_id=data.quiz_id,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    log_admin_action("lesson.create", admin.id, admin_email=admin.email, target_type="lesson", target_id=lesson.id, details={"title": lesson.title, "module_id": module_id}, db=db)
    return _serialize_lesson(lesson)


@router.patch("/{lesson_id}")
def update_lesson(
    lesson_id: int,
    data: LessonUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_course_writer),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    if module:
        _can_access_module(db, admin, module)

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    if "image_urls" in update_data:
        update_data["image_urls"] = json.dumps(update_data["image_urls"])

    if "module_id" in update_data and update_data["module_id"] != lesson.module_id:
        target_module = db.query(Module).filter(Module.id == update_data["module_id"]).first()
        if not target_module:
            raise HTTPException(status_code=404, detail="Target module not found")
        _can_access_module(db, admin, target_module)

    for field, value in update_data.items():
        if hasattr(lesson, field):
            setattr(lesson, field, value)

    db.commit()
    db.refresh(lesson)
    log_admin_action("lesson.update", admin.id, admin_email=admin.email, target_type="lesson", target_id=lesson.id, db=db)
    return _serialize_lesson(lesson)


@router.delete("/{lesson_id}", status_code=204)
def delete_lesson(lesson_id: int, db: Session = Depends(get_db), admin: User = Depends(require_course_writer)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    if module:
        _can_access_module(db, admin, module)
    db.delete(lesson)
    db.commit()
    log_admin_action("lesson.delete", admin.id, admin_email=admin.email, target_type="lesson", target_id=lesson_id, db=db)


@router.post("/reorder")
def reorder_lessons(
    body: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_course_writer),
):
    order = body.get("order", [])
    for idx, lesson_id in enumerate(order):
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if lesson:
            module = db.query(Module).filter(Module.id == lesson.module_id).first()
            if module:
                _can_access_module(db, admin, module)
            lesson.order = idx
    db.commit()
    return {"success": True}