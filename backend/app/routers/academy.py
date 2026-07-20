from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db import get_db
from app.auth import get_current_user
from app.models import User, Course, Module, Lesson, Quiz, QuizQuestion, QuizOption, Attempt
from app.schemas import (
    CourseCreate, CourseRead, CourseListRead,
    ModuleCreate, ModuleRead, ModuleDetailRead,
    LessonCreate, LessonRead,
    QuizCreate, QuizRead, QuizQuestionCreate, QuizQuestionRead,
    QuizOptionCreate, QuizOptionRead,
    AttemptCreate, AttemptRead,
)

router = APIRouter(tags=["Academy"])


@router.post("/courses", response_model=CourseRead)
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can create courses")

    course = Course(
        title=course_in.title,
        description=course_in.description,
        is_published=False,
        start_date=course_in.start_date,
        end_date=course_in.end_date,
        school_id=current_user.school_id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/courses")
def list_courses(
    published: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Course).filter(Course.school_id == current_user.school_id)
    if published is not None:
        query = query.filter(Course.is_published == published)
    elif current_user.role == "student":
        query = query.filter(Course.is_published == True)
    total = query.count()
    items = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/courses/{course_id}", response_model=CourseRead)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/courses/{course_id}/detail")
def get_course_detail(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order).all()
    module_list = []
    for mod in modules:
        lessons = db.query(Lesson).filter(Lesson.module_id == mod.id).order_by(Lesson.order).all()
        lesson_list = []
        for les in lessons:
            lesson_list.append({
                "id": les.id,
                "module_id": les.module_id,
                "title": les.title,
                "content": les.content or "",
                "duration_minutes": les.duration_minutes or 0,
                "video_url": les.video_url or "",
                "order": les.order,
            })
        module_list.append({
            "id": mod.id,
            "course_id": mod.course_id,
            "title": mod.title,
            "description": mod.description or "",
            "order": mod.order,
            "lessons": lesson_list,
        })

    from app.models import Progress
    progress_query = db.query(Progress).filter(
        Progress.school_id == current_user.school_id,
        Progress.user_id == current_user.id,
        Progress.course_id == course_id,
    )
    completed_lessons = {p.lesson_id for p in progress_query.filter(Progress.completed == True).all()}

    total_lessons = sum(len(m["lessons"]) for m in module_list)
    completed_count = len(completed_lessons)
    progress_pct = round(completed_count / total_lessons * 100, 1) if total_lessons > 0 else 0

    return {
        "id": course.id,
        "title": course.title,
        "description": course.description or "",
        "published": course.is_published,
        "start_date": course.start_date.isoformat() if course.start_date else None,
        "end_date": course.end_date.isoformat() if course.end_date else None,
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "modules": module_list,
        "progress": progress_pct,
        "completed_lessons": list(completed_lessons),
    }


@router.put("/courses/{course_id}", response_model=CourseRead)
def update_course(
    course_id: int,
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can update courses")

    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course.title = course_in.title
    course.description = course_in.description
    course.start_date = course_in.start_date
    course.end_date = course_in.end_date
    db.commit()
    db.refresh(course)
    return course


@router.put("/courses/{course_id}/publish")
def toggle_publish(
    course_id: int,
    published: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can publish courses")

    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course.is_published = published
    db.commit()
    db.refresh(course)
    return {"id": course.id, "published": course.is_published}


@router.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can delete courses")

    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.delete(course)
    db.commit()
    return {"ok": True}


# ---- Modules ----

@router.post("/modules", response_model=ModuleRead)
def create_module(
    module_in: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can create modules")

    course = db.query(Course).filter(
        Course.id == module_in.course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    max_order = db.query(Module).filter(Module.course_id == module_in.course_id).count()
    module = Module(
        course_id=module_in.course_id,
        title=module_in.title,
        description=module_in.description,
        order=module_in.order if module_in.order is not None else max_order,
        school_id=current_user.school_id,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


@router.put("/modules/{module_id}", response_model=ModuleRead)
def update_module(
    module_id: int,
    module_in: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can update modules")

    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    course = db.query(Course).filter(
        Course.id == module.course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Module does not belong to your school")

    module.title = module_in.title
    module.description = module_in.description
    module.order = module_in.order if module_in.order is not None else module.order
    db.commit()
    db.refresh(module)
    return module


@router.delete("/modules/{module_id}")
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can delete modules")

    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    course = db.query(Course).filter(
        Course.id == module.course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Module does not belong to your school")

    db.delete(module)
    db.commit()
    return {"ok": True}


@router.get("/courses/{course_id}/modules", response_model=list[ModuleRead])
def list_modules(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return db.query(Module).filter(Module.course_id == course_id).order_by(Module.order).all()


# ---- Lessons ----

@router.post("/lessons", response_model=LessonRead)
def create_lesson(
    lesson_in: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can create lessons")

    module = db.query(Module).filter(Module.id == lesson_in.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    course = db.query(Course).filter(
        Course.id == module.course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Module does not belong to your school")

    max_order = db.query(Lesson).filter(Lesson.module_id == lesson_in.module_id).count()
    lesson = Lesson(
        module_id=lesson_in.module_id,
        title=lesson_in.title,
        content=lesson_in.content,
        duration_minutes=lesson_in.duration_minutes,
        video_url=lesson_in.video_url,
        order=lesson_in.order if lesson_in.order is not None else max_order,
        school_id=current_user.school_id,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.put("/lessons/{lesson_id}", response_model=LessonRead)
def update_lesson(
    lesson_id: int,
    lesson_in: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can update lessons")

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    module = db.query(Module).filter(Module.id == lesson_in.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    course = db.query(Course).filter(
        Course.id == module.course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Lesson does not belong to your school")

    lesson.module_id = lesson_in.module_id
    lesson.title = lesson_in.title
    lesson.content = lesson_in.content
    lesson.duration_minutes = lesson_in.duration_minutes
    lesson.video_url = lesson_in.video_url
    lesson.order = lesson_in.order if lesson_in.order is not None else lesson.order
    db.commit()
    db.refresh(lesson)
    return lesson


@router.delete("/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can delete lessons")

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    course = db.query(Course).filter(
        Course.id == module.course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Lesson does not belong to your school")

    db.delete(lesson)
    db.commit()
    return {"ok": True}


@router.get("/lessons/{lesson_id}", response_model=LessonRead)
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    course = db.query(Course).filter(
        Course.id == module.course_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Lesson does not belong to your school")

    return lesson


@router.get("/lessons/{lesson_id}/quizzes", response_model=list[QuizRead])
def get_lesson_quizzes(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return db.query(Quiz).filter(Quiz.lesson_id == lesson_id).all()


# ---- Quizzes ----

@router.post("/quizzes", response_model=QuizRead)
def create_quiz(
    quiz_in: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can create quizzes")

    if quiz_in.lesson_id:
        lesson = db.query(Lesson).filter(Lesson.id == quiz_in.lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        module = db.query(Module).filter(Module.id == lesson.module_id).first()
        course = db.query(Course).filter(
            Course.id == module.course_id,
            Course.school_id == current_user.school_id,
        ).first()
        if not course:
            raise HTTPException(status_code=404, detail="Lesson does not belong to your school")

    quiz = Quiz(
        lesson_id=quiz_in.lesson_id,
        course_id=quiz_in.course_id,
        title=quiz_in.title,
        questions=quiz_in.questions,
        time_limit_minutes=quiz_in.time_limit_minutes,
        school_id=current_user.school_id,
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


@router.get("/quizzes/{quiz_id}", response_model=QuizRead)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Quiz does not belong to your school")
    return quiz


@router.get("/quizzes/{quiz_id}/questions", response_model=list[QuizQuestionRead])
def get_quiz_questions(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Quiz does not belong to your school")
    return db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.order).all()


@router.post("/quizzes/{quiz_id}/attempt", response_model=AttemptRead)
def start_quiz_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    attempt = Attempt(
        quiz_id=quiz_id,
        user_id=current_user.id,
        started_at=datetime.now(timezone.utc),
        status="in_progress",
        school_id=current_user.school_id,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.put("/quizzes/{quiz_id}/attempt/{attempt_id}", response_model=AttemptRead)
def submit_quiz_attempt(
    quiz_id: int,
    attempt_id: int,
    answers: list[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.query(Attempt).filter(
        Attempt.id == attempt_id,
        Attempt.quiz_id == quiz_id,
        Attempt.user_id == current_user.id,
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()

    score = 0.0
    total_points = 0.0
    for q in questions:
        total_points += q.points or 1.0
        user_answer = next((a for a in answers if a.get("question_id") == q.id), None)
        if user_answer:
            correct_option = db.query(QuizOption).filter(
                QuizOption.question_id == q.id,
                QuizOption.is_correct == True,
            ).first()
            if correct_option and user_answer.get("option_id") == correct_option.id:
                score += q.points or 1.0

    attempt.score = round(score / total_points * 100, 1) if total_points > 0 else 0.0
    attempt.finished_at = datetime.now(timezone.utc)
    attempt.status = "completed"
    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/quizzes/{quiz_id}/attempts")
def list_quiz_attempts(
    quiz_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    query = db.query(Attempt).filter(Attempt.quiz_id == quiz_id)
    if current_user.role == "student":
        query = query.filter(Attempt.user_id == current_user.id)
    total = query.count()
    items = query.order_by(Attempt.started_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/my-courses")
def my_courses(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "student":
        courses_query = db.query(Course).filter(
            Course.school_id == current_user.school_id,
            Course.is_published == True,
        )
    else:
        courses_query = db.query(Course).filter(
            Course.school_id == current_user.school_id,
        )

    total = courses_query.count()
    courses = courses_query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for course in courses:
        modules = db.query(Module).filter(Module.course_id == course.id).all()
        total_lessons = db.query(Lesson).filter(Lesson.module_id.in_([m.id for m in modules])).count()
        result.append({
            "id": course.id,
            "title": course.title,
            "description": course.description or "",
            "published": course.is_published,
            "module_count": len(modules),
            "lesson_count": total_lessons,
        })
    return {"total": total, "skip": skip, "limit": limit, "items": result}