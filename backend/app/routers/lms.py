from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db import get_db
from app.auth import get_current_user
from app.deps import check_school_access, require_active_subscription
from app.models import User, Assignment, ClassRoom, Submission, ClassroomEnrollment, Progress, UserRole
from app.schemas import (
    AssignmentCreate, AssignmentRead, SubmissionCreate, SubmissionRead,
    SubmissionResult, ProgressCreate, ProgressRead, EnrollmentCreate, EnrollmentRead,
)

router = APIRouter(tags=["LMS"])


def _role_str(user) -> str:
    val = user.role.value if hasattr(user.role, "value") else str(user.role)
    return val.lower()


def _is_teacher(user) -> bool:
    return _role_str(user) == "teacher"


def _is_admin_or_teacher(user) -> bool:
    return _role_str(user) in ("admin_school", "pedagogical_admin", "pedagogical_lead", "super_admin", "teacher")


def _is_super_user(user) -> bool:
    return _role_str(user) == "super_admin"


@router.post("/assignments", response_model=AssignmentRead)
def create_assignment(
    assignment_in: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _sub=Depends(require_active_subscription),
):
    if not _is_admin_or_teacher(current_user):
        raise HTTPException(status_code=403, detail="Only teachers or admins can create assignments")

    class_room = db.query(ClassRoom).filter(
        ClassRoom.id == assignment_in.class_id,
        ClassRoom.school_id == current_user.school_id,
    ).first()
    if not class_room:
        raise HTTPException(status_code=404, detail="Class not found")

    assignment = Assignment(
        class_id=assignment_in.class_id,
        title=assignment_in.title,
        description=assignment_in.description,
        due_date=assignment_in.due_date,
        school_id=current_user.school_id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/assignments")
def list_assignments(
    class_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Assignment).join(ClassRoom, Assignment.classroom_id == ClassRoom.id).filter(ClassRoom.school_id == current_user.school_id)
    if class_id:
        query = query.filter(Assignment.classroom_id == class_id)
    total = query.count()
    items = query.order_by(Assignment.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.school_id == current_user.school_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.put("/assignments/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: int,
    assignment_in: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin_or_teacher(current_user):
        raise HTTPException(status_code=403, detail="Only teachers or admins can update assignments")

    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.school_id == current_user.school_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.title = assignment_in.title
    assignment.description = assignment_in.description
    assignment.due_date = assignment_in.due_date
    assignment.class_id = assignment_in.class_id
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin_or_teacher(current_user):
        raise HTTPException(status_code=403, detail="Only teachers or admins can delete assignments")

    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.school_id == current_user.school_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(assignment)
    db.commit()
    return {"ok": True}


@router.post("/assignments/{assignment_id}/submit", response_model=SubmissionResult)
def submit_assignment(
    assignment_id: int,
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.school_id == current_user.school_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    existing = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already submitted this assignment")

    submission = Submission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        content=submission_in.content,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    try:
        from app.ai import RAGService
        rag = RAGService()
        ai_result = rag.auto_correct(
            school_id=current_user.school_id,
            assignment_text=submission_in.content,
            question=assignment.title,
        )
        submission.ai_feedback = ai_result.get("feedback", "")
        db.commit()
        feedback = ai_result.get("feedback", "")
    except Exception:
        feedback = "AI grading is currently unavailable. Your submission has been received."

    return SubmissionResult(
        id=submission.id,
        assignment_id=assignment_id,
        content=submission.content,
        grade=None,
        ai_feedback=feedback,
        submitted_at=submission.submitted_at,
    )


@router.get("/submissions")
def list_submissions(
    assignment_id: int | None = None,
    student_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Submission).join(Assignment).filter(
        Assignment.school_id == current_user.school_id
    )
    if _role_str(current_user) == "student":
        query = query.filter(Submission.student_id == current_user.id)
    if assignment_id:
        query = query.filter(Submission.assignment_id == assignment_id)
    if student_id and _is_admin_or_teacher(current_user):
        query = query.filter(Submission.student_id == student_id)
    total = query.count()
    items = query.order_by(Submission.submitted_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/submissions/{submission_id}", response_model=SubmissionRead)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).join(Assignment).filter(
        Submission.id == submission_id,
        Assignment.school_id == current_user.school_id,
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if _role_str(current_user) == "student" and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your submission")
    return submission


@router.put("/submissions/{submission_id}/grade")
def grade_submission(
    submission_id: int,
    grade: float,
    ai_feedback: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin_or_teacher(current_user):
        raise HTTPException(status_code=403, detail="Only teachers or admins can grade")

    submission = db.query(Submission).join(Assignment).filter(
        Submission.id == submission_id,
        Assignment.school_id == current_user.school_id,
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    submission.grade = grade
    if ai_feedback is not None:
        submission.ai_feedback = ai_feedback
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/classes", response_model=list[dict])
def list_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    classes = db.query(ClassRoom).filter(ClassRoom.school_id == current_user.school_id).all()
    result = []
    for cls in classes:
        student_count = db.query(ClassroomEnrollment).filter(ClassroomEnrollment.classroom_id == cls.id).count()
        assignment_count = db.query(Assignment).filter(Assignment.classroom_id == cls.id).count()
        result.append({
            "id": cls.id,
            "name": cls.name,
            "code": cls.invite_code or "",
            "description": cls.description or "",
            "student_count": student_count,
            "assignment_count": assignment_count,
        })
    return result


@router.post("/enrollments", response_model=EnrollmentRead)
def create_enrollment(
    enrollment_in: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin_or_teacher(current_user):
        raise HTTPException(status_code=403, detail="Only teachers or admins can enroll students")

    class_room = db.query(ClassRoom).filter(
        ClassRoom.id == enrollment_in.classroom_id,
        ClassRoom.school_id == current_user.school_id,
    ).first()
    if not class_room:
        raise HTTPException(status_code=404, detail="Class not found")

    existing = db.query(ClassroomEnrollment).filter(
        ClassroomEnrollment.classroom_id == enrollment_in.classroom_id,
        ClassroomEnrollment.student_id == enrollment_in.student_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already enrolled")

    enrollment = ClassroomEnrollment(
        classroom_id=enrollment_in.classroom_id,
        student_id=enrollment_in.student_id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.get("/enrollments")
def list_enrollments(
    class_id: int | None = None,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import join
    query = db.query(ClassroomEnrollment).join(ClassRoom, ClassroomEnrollment.classroom_id == ClassRoom.id)
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN_SCHOOL):
        query = query.filter(ClassRoom.school_id == current_user.school_id)
    if class_id:
        query = query.filter(ClassroomEnrollment.classroom_id == class_id)
    if user_id:
        query = query.filter(ClassroomEnrollment.student_id == user_id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.delete("/enrollments/{enrollment_id}")
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin_or_teacher(current_user):
        raise HTTPException(status_code=403, detail="Only teachers or admins can remove enrollments")

    enrollment = db.query(ClassroomEnrollment).filter(
        ClassroomEnrollment.id == enrollment_id,
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    # School isolation: admin/teacher can only delete enrollments in their school
    if not _is_super_user(current_user):
        if enrollment.school_id and enrollment.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="Access denied")

    db.delete(enrollment)
    db.commit()
    return {"ok": True}


@router.get("/my-classes", response_model=list[dict])
def my_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if _role_str(current_user) == "student":
        enrollments = db.query(ClassroomEnrollment).filter(
            ClassroomEnrollment.student_id == current_user.id,
        ).all()
        result = []
        for e in enrollments:
            cls = db.query(ClassRoom).filter(ClassRoom.id == e.classroom_id).first()
            if cls:
                pending_assignments = db.query(Assignment).filter(
                    Assignment.classroom_id == cls.id,
                    Assignment.due_date > datetime.now(timezone.utc),
                ).count()
                result.append({
                    "id": cls.id,
                    "name": cls.name,
                    "code": cls.invite_code or "",
                    "pending_assignments": pending_assignments,
                    "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
                })
        return result
    else:
        classes = db.query(ClassRoom).filter(ClassRoom.school_id == current_user.school_id).all()
        result = []
        for cls in classes:
            student_count = db.query(ClassroomEnrollment).filter(ClassroomEnrollment.classroom_id == cls.id).count()
            result.append({
                "id": cls.id,
                "name": cls.name,
                "code": cls.invite_code or "",
                "student_count": student_count,
            })
        return result


@router.get("/progress")
def my_progress(
    course_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Progress).filter(
        Progress.school_id == current_user.school_id,
        Progress.user_id == current_user.id,
    )
    if course_id:
        query = query.filter(Progress.course_id == course_id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.post("/progress", response_model=ProgressRead)
def mark_progress(
    progress_in: ProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Progress).filter(
        Progress.school_id == current_user.school_id,
        Progress.user_id == current_user.id,
        Progress.lesson_id == progress_in.lesson_id,
    ).first()

    if existing:
        existing.completed = progress_in.completed
        if progress_in.completed:
            existing.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    progress = Progress(
        user_id=current_user.id,
        course_id=progress_in.course_id,
        lesson_id=progress_in.lesson_id,
        completed=progress_in.completed,
        completed_at=datetime.now(timezone.utc) if progress_in.completed else None,
        school_id=current_user.school_id,
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


@router.get("/classes/{class_id}/available-students")
def list_available_students(
    class_id: int,
    search: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrolled_ids = [
        e.student_id for e in db.query(ClassroomEnrollment).filter(
            ClassroomEnrollment.classroom_id == class_id
        ).all()
    ]

    class_room = db.query(ClassRoom).filter(ClassRoom.id == class_id).first()
    if not class_room:
        raise HTTPException(status_code=404, detail="Class not found")
    check_school_access(current_user, class_room.school_id)

    from sqlalchemy import or_

    query = db.query(User).filter(
        User.id.notin_(enrolled_ids) if enrolled_ids else True,
    )

    role_val = current_user.role
    role_str = role_val.value if hasattr(role_val, "value") else str(role_val)

    query = query.filter(User.role == UserRole.STUDENT)

    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN_SCHOOL):
        query = query.filter(User.school_id == current_user.school_id)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_filter),
                User.email.ilike(search_filter),
            )
        )

    students = query.limit(50).all()
    return [
        {"id": s.id, "full_name": s.full_name or s.email, "email": s.email, "school_id": s.school_id}
        for s in students
    ]


@router.get("/classes/{class_id}/students")
def list_class_students(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    classroom = db.query(ClassRoom).filter(ClassRoom.id == class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    check_school_access(current_user, classroom.school_id)

    enrollments = db.query(ClassroomEnrollment).filter(
        ClassroomEnrollment.classroom_id == class_id,
    ).all()
    result = []
    for e in enrollments:
        student = db.query(User).filter(User.id == e.student_id).first()
        result.append({
            "id": e.id,
            "student_id": e.student_id,
            "full_name": student.full_name if student else None,
            "email": student.email if student else None,
            "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
            "status": e.status.value if hasattr(e.status, 'value') else e.status,
        })
    return result


class CreateAssignmentRequest(BaseModel):
    title: str
    description: str = ""
    due_date: str = ""


@router.post("/classes/{class_id}/assignments")
def create_class_assignment(
    class_id: int,
    body: CreateAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _sub=Depends(require_active_subscription),
):
    raw_role = current_user.role
    user_role = str(raw_role.value).lower() if hasattr(raw_role, 'value') else str(raw_role).lower()
    if user_role not in ("teacher", "admin_school", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can create assignments")

    class_room = db.query(ClassRoom).filter(
        ClassRoom.id == class_id,
        ClassRoom.school_id == current_user.school_id,
    ).first()
    if not class_room:
        raise HTTPException(status_code=404, detail="Class not found")

    due = None
    if body.due_date:
        try:
            from datetime import datetime as dt
            due = dt.fromisoformat(body.due_date.replace("Z", "+00:00"))
        except Exception:
            pass

    a = Assignment(
        classroom_id=class_id,
        title=body.title,
        description=body.description or None,
        due_date=due,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return {
        "id": a.id,
        "title": a.title,
        "description": a.description,
        "due_date": a.due_date.isoformat() if a.due_date else None,
    }


@router.get("/classes/{class_id}/assignments")
def list_class_assignments(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    class_room = db.query(ClassRoom).filter(ClassRoom.id == class_id).first()
    if not class_room:
        raise HTTPException(status_code=404, detail="Class not found")
    check_school_access(current_user, class_room.school_id)
    assignments = db.query(Assignment).filter(Assignment.classroom_id == class_id).all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "due_date": a.due_date.isoformat() if a.due_date else None,
        }
        for a in assignments
    ]


class CreateClassRequest(BaseModel):
    name: str


@router.post("/classes")
def create_class(
    body: CreateClassRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin_or_teacher(current_user):
        raise HTTPException(status_code=403, detail="Only teachers or admins can create classes")
    import secrets as _secrets
    cls = ClassRoom(
        name=body.name,
        school_id=current_user.school_id,
        teacher_id=current_user.id,
        invite_code=_secrets.token_urlsafe(8),
    )
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return {"id": cls.id, "name": cls.name}


@router.delete("/classes/{class_id}")
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin_or_teacher(current_user):
        raise HTTPException(status_code=403, detail="Only teachers or admins can delete classes")
    cls = db.query(ClassRoom).filter(ClassRoom.id == class_id, ClassRoom.school_id == current_user.school_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(cls)
    db.commit()
    return {"ok": True}


@router.delete("/classes/{class_id}/students/{student_id}")
def remove_student_from_class(
    class_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin_or_teacher(current_user):
        raise HTTPException(status_code=403, detail="Only teachers or admins can remove students")
    classroom = db.query(ClassRoom).filter(ClassRoom.id == class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    check_school_access(current_user, classroom.school_id)
    enrollment = db.query(ClassroomEnrollment).filter(
        ClassroomEnrollment.id == student_id,
        ClassroomEnrollment.classroom_id == class_id,
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    db.delete(enrollment)
    db.commit()
    return {"ok": True}