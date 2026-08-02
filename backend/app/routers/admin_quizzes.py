"""Quiz builder API for admin-side quiz management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.auth import get_current_user
from app.db import get_db
from app.deps import require_admin, check_school_access, get_user_role, require_active_subscription
from app.audit import log_admin_action
from app.models import Course, Module, Lesson, Quiz, QuizQuestion, QuizOption, User


router = APIRouter(tags=["Admin Quizzes"])


class OptionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    is_correct: bool = False


class QuestionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    question_type: str = Field(default="single")
    points: float = Field(default=1.0, ge=0)
    order: int | None = None
    options: list[OptionCreate] = []


class QuestionUpdate(BaseModel):
    text: str | None = Field(None, min_length=1, max_length=2000)
    question_type: str | None = None
    points: float | None = Field(None, ge=0)
    order: int | None = None

    model_config = ConfigDict(extra="allow")


class QuizCreate(BaseModel):
    lesson_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    time_limit_minutes: int | None = Field(default=30, ge=0)
    passing_score_percent: float = Field(default=60.0, ge=0, le=100)
    max_attempts: int | None = Field(default=3, ge=1)
    show_correct_answers: bool = True


class QuizUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    time_limit_minutes: int | None = Field(None, ge=0)
    passing_score_percent: float | None = Field(None, ge=0, le=100)
    max_attempts: int | None = Field(None, ge=1)
    show_correct_answers: bool | None = None

    model_config = ConfigDict(extra="allow")


def _can_access_lesson(db: Session, admin: User, lesson_id: int) -> Lesson:
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    role = get_user_role(admin)
    if role == "super_admin":
        return lesson
    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    if module:
        course = db.query(Course).filter(Course.id == module.course_id).first()
        if course and course.school_id != admin.school_id:
            raise HTTPException(status_code=403, detail="Access denied")
    return lesson


def _serialize_option(option: QuizOption) -> dict:
    return {
        "id": option.id,
        "text": option.option_text,
        "is_correct": bool(option.is_correct),
        "order": option.order_index or 0,
    }


def _serialize_question(question: QuizQuestion) -> dict:
    return {
        "id": question.id,
        "text": question.question_text,
        "question_type": question.question_type or "multiple_choice",
        "points": question.points or 1.0,
        "order": question.order_index or 0,
        "options": [_serialize_option(o) for o in (question.options or [])],
    }


def _serialize_quiz(db: Session, quiz: Quiz, include_questions: bool = True) -> dict:
    data = {
        "id": quiz.id,
        "lesson_id": quiz.lesson_id,
        "title": quiz.title,
        "description": quiz.description,
        "time_limit_minutes": (quiz.time_limit_seconds // 60) if quiz.time_limit_seconds else None,
        "passing_score_percent": quiz.passing_score_percent or 60.0,
        "max_attempts": quiz.max_attempts,
        "show_correct_answers": quiz.show_correct_answers if quiz.show_correct_answers is not None else True,
        "created_at": str(quiz.created_at) if quiz.created_at else None,
    }
    if include_questions:
        questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.order_index).all()
        data["questions"] = [_serialize_question(q) for q in questions]
    return data


# ---- Routes ----

@router.get("/lesson/{lesson_id}")
def get_quiz_by_lesson(lesson_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    _can_access_lesson(db, admin, lesson_id)
    quiz = db.query(Quiz).filter(Quiz.lesson_id == lesson_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found for this lesson")
    return _serialize_quiz(db, quiz)


@router.get("/{quiz_id}")
def get_quiz(quiz_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    # Verify school access via quiz -> lesson -> school_id
    if quiz.lesson_id:
        lesson = db.query(Lesson).filter(Lesson.id == quiz.lesson_id).first()
        if lesson and lesson.school_id:
            check_school_access(admin, lesson.school_id)
    return _serialize_quiz(db, quiz)


@router.post("", status_code=201)
def create_quiz(data: QuizCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin), _sub=Depends(require_active_subscription)):
    lesson = _can_access_lesson(db, admin, data.lesson_id) if hasattr(data, 'lesson_id') and data.lesson_id else None

    if not hasattr(data, 'lesson_id') or not data.lesson_id:
        raise HTTPException(status_code=422, detail="lesson_id is required")

    existing = db.query(Quiz).filter(Quiz.lesson_id == data.lesson_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Quiz already exists for this lesson")

    quiz = Quiz(
        school_id=admin.school_id,
        lesson_id=data.lesson_id,
        title=data.title,
        description=data.description,
        time_limit_seconds=(data.time_limit_minutes or 0) * 60 if data.time_limit_minutes else None,
        passing_score_percent=data.passing_score_percent,
        max_attempts=data.max_attempts,
        show_correct_answers=data.show_correct_answers,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    log_admin_action("quiz.create", admin.id, admin_email=admin.email, target_type="quiz", target_id=quiz.id, details={"title": quiz.title, "lesson_id": quiz.lesson_id}, db=db)
    return _serialize_quiz(db, quiz)


@router.patch("/{quiz_id}")
def update_quiz(quiz_id: int, data: QuizUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _can_access_lesson(db, admin, quiz.lesson_id)

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    if "time_limit_minutes" in update_data:
        update_data["time_limit_seconds"] = update_data.pop("time_limit_minutes") * 60
    for field, value in update_data.items():
        if hasattr(quiz, field):
            setattr(quiz, field, value)

    db.commit()
    db.refresh(quiz)
    log_admin_action("quiz.update", admin.id, admin_email=admin.email, target_type="quiz", target_id=quiz.id, db=db)
    return _serialize_quiz(db, quiz)


@router.delete("/{quiz_id}", status_code=204)
def delete_quiz(quiz_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _can_access_lesson(db, admin, quiz.lesson_id)
    db.delete(quiz)
    db.commit()
    log_admin_action("quiz.delete", admin.id, admin_email=admin.email, target_type="quiz", target_id=quiz_id, db=db)


# ---- Questions ----

@router.post("/{quiz_id}/questions", status_code=201)
def create_question(
    quiz_id: int,
    data: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _can_access_lesson(db, admin, quiz.lesson_id)

    max_order = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).count()

    question = QuizQuestion(
        quiz_id=quiz_id,
        question_text=data.text,
        question_type=data.question_type,
        points=data.points,
        order_index=data.order if data.order is not None else max_order,
    )
    db.add(question)
    db.flush()

    for idx, opt_data in enumerate(data.options):
        option = QuizOption(
            question_id=question.id,
            option_text=opt_data.text,
            is_correct=opt_data.is_correct,
            order=idx,
        )
        db.add(option)

    db.commit()
    db.refresh(question)
    return _serialize_question(question)


@router.patch("/{quiz_id}/questions/{question_id}")
def update_question(
    quiz_id: int,
    question_id: int,
    data: QuestionUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _can_access_lesson(db, admin, quiz.lesson_id)

    question = db.query(QuizQuestion).filter(
        QuizQuestion.id == question_id,
        QuizQuestion.quiz_id == quiz_id,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if hasattr(question, field):
            setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return _serialize_question(question)


@router.delete("/{quiz_id}/questions/{question_id}", status_code=204)
def delete_question(
    quiz_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _can_access_lesson(db, admin, quiz.lesson_id)

    question = db.query(QuizQuestion).filter(
        QuizQuestion.id == question_id,
        QuizQuestion.quiz_id == quiz_id,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(question)
    db.commit()


@router.post("/{quiz_id}/questions/{question_id}/options", status_code=201)
def add_option(
    quiz_id: int,
    question_id: int,
    data: OptionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _can_access_lesson(db, admin, quiz.lesson_id)

    question = db.query(QuizQuestion).filter(
        QuizQuestion.id == question_id,
        QuizQuestion.quiz_id == quiz_id,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    max_order = db.query(QuizOption).filter(QuizOption.question_id == question_id).count()
    option = QuizOption(
        question_id=question_id,
        option_text=data.text,
        is_correct=data.is_correct,
        order_index=max_order,
    )
    db.add(option)
    db.commit()
    db.refresh(option)
    return _serialize_option(option)


@router.delete("/{quiz_id}/questions/{question_id}/options/{option_id}", status_code=204)
def delete_option(
    quiz_id: int,
    question_id: int,
    option_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _can_access_lesson(db, admin, quiz.lesson_id)

    option = db.query(QuizOption).filter(
        QuizOption.id == option_id,
        QuizOption.question_id == question_id,
    ).first()
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")

    db.delete(option)
    db.commit()