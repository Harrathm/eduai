"""Chapter API backed by the existing modules table."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.deps import require_admin, get_user_role, require_active_subscription
from app.audit import log_admin_action
from app.models import Course, Module, User


router = APIRouter(tags=["Admin Chapters"])


class ChapterCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order: int | None = None


class ChapterUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    order: int | None = None

    model_config = ConfigDict(extra="allow")


class ChapterReorder(BaseModel):
    order: list[int]


def _can_access_course(db: Session, admin: User, course_id: int) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    role = get_user_role(admin)
    if role == "super_admin":
        return course
    if course.school_id != admin.school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return course


@router.get("")
def list_chapters(
    course_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    _can_access_course(db, admin, course_id)
    query = db.query(Module).filter(Module.course_id == course_id)
    total = query.count()
    chapters = query.order_by(Module.order).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": c.id,
                "course_id": c.course_id,
                "title": c.title,
                "description": c.description,
                "order": c.order or 0,
                "order_index": c.order or 0,
                "created_at": str(c.created_at) if c.created_at else None,
                "lessons": [],
            }
            for c in chapters
        ],
    }


@router.get("/{chapter_id}")
def get_chapter(chapter_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    chapter = db.query(Module).filter(Module.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    _can_access_course(db, admin, chapter.course_id)
    return {
        "id": chapter.id,
        "course_id": chapter.course_id,
        "title": chapter.title,
        "description": chapter.description,
        "order": chapter.order or 0,
        "order_index": chapter.order or 0,
        "created_at": str(chapter.created_at) if chapter.created_at else None,
        "lessons": [],
    }


@router.post("")
def create_chapter(course_id: int, data: ChapterCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin), _sub=Depends(require_active_subscription)):
    _can_access_course(db, admin, course_id)
    max_order = db.query(Module).filter(Module.course_id == course_id).count()
    chapter = Module(
        course_id=course_id,
        title=data.title,
        description=data.description,
        order=data.order if data.order is not None else max_order,
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    log_admin_action("chapter.create", admin.id, admin_email=admin.email, target_type="chapter", target_id=chapter.id, details={"title": chapter.title, "course_id": course_id}, db=db)
    return {
        "id": chapter.id,
        "course_id": chapter.course_id,
        "title": chapter.title,
        "description": chapter.description,
        "order": chapter.order or 0,
        "order_index": chapter.order or 0,
        "created_at": str(chapter.created_at) if chapter.created_at else None,
        "lessons": [],
    }


@router.patch("/{chapter_id}")
def update_chapter(chapter_id: int, data: ChapterUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    chapter = db.query(Module).filter(Module.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    _can_access_course(db, admin, chapter.course_id)

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if hasattr(chapter, field):
            setattr(chapter, field, value)

    db.commit()
    db.refresh(chapter)
    log_admin_action("chapter.update", admin.id, admin_email=admin.email, target_type="chapter", target_id=chapter.id, db=db)
    return {
        "id": chapter.id,
        "course_id": chapter.course_id,
        "title": chapter.title,
        "description": chapter.description,
        "order": chapter.order or 0,
        "order_index": chapter.order or 0,
        "created_at": str(chapter.created_at) if chapter.created_at else None,
        "lessons": [],
    }


@router.delete("/{chapter_id}")
def delete_chapter(chapter_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    chapter = db.query(Module).filter(Module.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    _can_access_course(db, admin, chapter.course_id)
    db.delete(chapter)
    db.commit()
    log_admin_action("chapter.delete", admin.id, admin_email=admin.email, target_type="chapter", target_id=chapter_id, db=db)


@router.post("/reorder")
def reorder_chapters(data: ChapterReorder, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    for idx, chapter_id in enumerate(data.order):
        chapter = db.query(Module).filter(Module.id == chapter_id).first()
        if chapter:
            _can_access_course(db, admin, chapter.course_id)
            chapter.order = idx
    db.commit()
    return {"success": True}