from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional, List

from app.db import get_db
from app.auth import get_current_user
from app.models import (
    User, TeacherClass, ClassCourseAccess, ClassParcoursAccess, StudentEnrollment, Course, School,
    CourseEnrollment, QuizAttempt, Quiz, Lesson, Module, Abonnement, PackDefinition,
    Parcours, Message, MessageType,
)
from app.schemas import (
    TeacherClassCreate, TeacherClassUpdate, TeacherClassRead,
    ClassCourseAccessRead, StudentEnrollmentRead,
)

teacher_router = APIRouter()
admin_teacher_router = APIRouter()


# ─── Helpers ────────────────────────────────────────────────────────────

def _require_teacher(current_user: User = Depends(get_current_user)):
    raw = current_user.role
    role = str(raw.value).upper() if hasattr(raw, 'value') else str(raw).upper().replace('USERROLE.', '')
    if role not in ("TEACHER", "SUPER_ADMIN", "ADMIN_SCHOOL", "PEDAGOGICAL_ADMIN", "PEDAGOGICAL_LEAD"):
        raise HTTPException(status_code=403, detail="Teacher access required")
    return current_user


def _require_super_admin_for_teacher(current_user: User = Depends(get_current_user)):
    raw = current_user.role
    role = str(raw.value).upper() if hasattr(raw, 'value') else str(raw).upper().replace('USERROLE.', '')
    if role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return current_user


def _own_class_or_403(db: Session, class_id: int, teacher_id: int):
    tc = db.query(TeacherClass).filter(TeacherClass.id == class_id, TeacherClass.teacher_id == teacher_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Class not found or not owned by you")
    return tc


def _serialize_tc(tc: TeacherClass, db: Session) -> dict:
    courses_count = db.query(func.count(ClassCourseAccess.id)).filter(
        ClassCourseAccess.class_id == tc.id, ClassCourseAccess.is_active == True
    ).scalar() or 0
    parcours_count = db.query(func.count(ClassParcoursAccess.id)).filter(
        ClassParcoursAccess.class_id == tc.id, ClassParcoursAccess.is_active == True
    ).scalar() or 0
    students_count = db.query(func.count(StudentEnrollment.id)).filter(
        StudentEnrollment.class_id == tc.id, StudentEnrollment.is_active == True
    ).scalar() or 0
    teacher_name = tc.teacher.full_name if tc.teacher else None
    school_name = tc.school.name if tc.school else None
    return {
        "id": tc.id,
        "teacher_id": tc.teacher_id,
        "school_id": tc.school_id,
        "teacher_name": teacher_name,
        "school_name": school_name,
        "name": tc.name,
        "description": tc.description,
        "code": tc.code,
        "is_active": tc.is_active,
        "created_at": tc.created_at,
        "updated_at": tc.updated_at,
        "courses_count": courses_count,
        "parcours_count": parcours_count,
        "students_count": students_count,
    }


# ═══════════════════════════════════════════════════════════════════════
# TEACHER-FACING ENDPOINTS  (/api/teacher)
# ═══════════════════════════════════════════════════════════════════════

@teacher_router.get("/courses")
def list_my_teacher_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: list courses authored by the current user."""
    courses = db.query(Course).filter(Course.author_id == current_user.id).order_by(Course.created_at.desc()).all()
    result = []
    for c in courses:
        result.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "status": c.status.value if hasattr(c.status, "value") else c.status,
            "category_cible": c.category_cible,
            "niveau_scolaire": c.niveau_scolaire,
            "visibility": c.visibility,
        })
    return result


# ═══════════════════════════════════════════════════════════════════════
# TEACHER CLASSES  (/api/teacher/classes)
# ═══════════════════════════════════════════════════════════════════════

@teacher_router.get("/classes", response_model=List[TeacherClassRead])
def list_my_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: list all my classes."""
    classes = db.query(TeacherClass).filter(
        TeacherClass.teacher_id == current_user.id
    ).order_by(TeacherClass.created_at.desc()).all()
    return [_serialize_tc(tc, db) for tc in classes]


@teacher_router.post("/classes", response_model=TeacherClassRead)
def create_class(
    body: TeacherClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: create a new class."""
    tc = TeacherClass(
        teacher_id=current_user.id,
        school_id=current_user.school_id,
        name=body.name,
        description=body.description,
        code=body.code,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return _serialize_tc(tc, db)


@teacher_router.get("/classes/{class_id}", response_model=TeacherClassRead)
def get_my_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: get details of one of my classes."""
    tc = _own_class_or_403(db, class_id, current_user.id)
    return _serialize_tc(tc, db)


@teacher_router.put("/classes/{class_id}", response_model=TeacherClassRead)
def update_my_class(
    class_id: int,
    body: TeacherClassUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: update one of my classes."""
    tc = _own_class_or_403(db, class_id, current_user.id)
    if body.name is not None:
        tc.name = body.name
    if body.description is not None:
        tc.description = body.description
    if body.code is not None:
        tc.code = body.code
    if body.is_active is not None:
        tc.is_active = body.is_active
    tc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(tc)
    return _serialize_tc(tc, db)


@teacher_router.delete("/classes/{class_id}")
def delete_my_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: delete one of my classes."""
    tc = _own_class_or_403(db, class_id, current_user.id)
    db.delete(tc)
    db.commit()
    return {"ok": True, "deleted_id": class_id}


# ─── Teacher Class → Courses ─────────────────────────────────────────

@teacher_router.get("/classes/{class_id}/courses", response_model=List[ClassCourseAccessRead])
def list_class_courses(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: list courses assigned to a class."""
    _own_class_or_403(db, class_id, current_user.id)
    accesses = db.query(ClassCourseAccess).filter(
        ClassCourseAccess.class_id == class_id,
        ClassCourseAccess.is_active == True,
    ).all()
    result = []
    for a in accesses:
        course = db.query(Course).filter(Course.id == a.course_id).first()
        result.append({
            "id": a.id,
            "class_id": a.class_id,
            "course_id": a.course_id,
            "course_title": course.title if course else None,
            "assigned_at": a.assigned_at,
            "is_active": a.is_active,
        })
    return result


class AssignCourseRequest(BaseModel):
    course_id: int


@teacher_router.post("/classes/{class_id}/courses", response_model=ClassCourseAccessRead)
def assign_course_to_class(
    class_id: int,
    body: AssignCourseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: assign a course to a class. Only the teacher's own courses can be assigned."""
    _own_class_or_403(db, class_id, current_user.id)
    course = db.query(Course).filter(Course.id == body.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only assign your own courses")
    existing = db.query(ClassCourseAccess).filter(
        ClassCourseAccess.class_id == class_id,
        ClassCourseAccess.course_id == body.course_id,
    ).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
        course_title = course.title if course else None
        return {
            "id": existing.id,
            "class_id": existing.class_id,
            "course_id": existing.course_id,
            "course_title": course_title,
            "assigned_at": existing.assigned_at,
            "is_active": existing.is_active,
        }
    access = ClassCourseAccess(
        class_id=class_id,
        course_id=body.course_id,
    )
    db.add(access)
    db.commit()
    db.refresh(access)
    return {
        "id": access.id,
        "class_id": access.class_id,
        "course_id": access.course_id,
        "course_title": course.title if course else None,
        "assigned_at": access.assigned_at,
        "is_active": access.is_active,
    }


@teacher_router.delete("/classes/{class_id}/courses/{course_id}")
def remove_course_from_class(
    class_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: remove a course from a class."""
    _own_class_or_403(db, class_id, current_user.id)
    access = db.query(ClassCourseAccess).filter(
        ClassCourseAccess.class_id == class_id,
        ClassCourseAccess.course_id == course_id,
    ).first()
    if not access:
        raise HTTPException(status_code=404, detail="Course not assigned to this class")
    access.is_active = False
    db.commit()
    return {"ok": True, "action": "removed"}


# ─── Teacher Class → Parcours ────────────────────────────────────────

class AssignParcoursRequest(BaseModel):
    parcours_id: int


@teacher_router.get("/classes/{class_id}/parcours")
def list_class_parcours(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: list parcours assigned to a class."""
    _own_class_or_403(db, class_id, current_user.id)
    accesses = db.query(ClassParcoursAccess).filter(
        ClassParcoursAccess.class_id == class_id,
        ClassParcoursAccess.is_active == True,
    ).all()
    result = []
    for a in accesses:
        parcours = db.query(Parcours).filter(Parcours.id == a.parcours_id).first()
        result.append({
            "id": a.id,
            "class_id": a.class_id,
            "parcours_id": a.parcours_id,
            "parcours_titre": parcours.titre if parcours else None,
            "parcours_matiere": parcours.matiere if parcours else None,
            "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
            "is_active": a.is_active,
        })
    return result


@teacher_router.post("/classes/{class_id}/parcours")
def assign_parcours_to_class(
    class_id: int,
    body: AssignParcoursRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: assign a parcours to a class. Only the teacher's own parcours can be assigned."""
    _own_class_or_403(db, class_id, current_user.id)
    parcours = db.query(Parcours).filter(Parcours.id == body.parcours_id).first()
    if not parcours:
        raise HTTPException(status_code=404, detail="Parcours not found")
    if parcours.auteur_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only assign your own parcours")
    existing = db.query(ClassParcoursAccess).filter(
        ClassParcoursAccess.class_id == class_id,
        ClassParcoursAccess.parcours_id == body.parcours_id,
    ).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
        return {
            "id": existing.id,
            "class_id": existing.class_id,
            "parcours_id": existing.parcours_id,
            "parcours_titre": parcours.titre,
            "parcours_matiere": parcours.matiere,
            "assigned_at": existing.assigned_at.isoformat() if existing.assigned_at else None,
            "is_active": existing.is_active,
        }
    access = ClassParcoursAccess(
        class_id=class_id,
        parcours_id=body.parcours_id,
    )
    db.add(access)
    db.commit()
    db.refresh(access)
    return {
        "id": access.id,
        "class_id": access.class_id,
        "parcours_id": access.parcours_id,
        "parcours_titre": parcours.titre,
        "parcours_matiere": parcours.matiere,
        "assigned_at": access.assigned_at.isoformat() if access.assigned_at else None,
        "is_active": access.is_active,
    }


@teacher_router.delete("/classes/{class_id}/parcours/{parcours_id}")
def remove_parcours_from_class(
    class_id: int,
    parcours_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: remove a parcours from a class."""
    _own_class_or_403(db, class_id, current_user.id)
    access = db.query(ClassParcoursAccess).filter(
        ClassParcoursAccess.class_id == class_id,
        ClassParcoursAccess.parcours_id == parcours_id,
    ).first()
    if not access:
        raise HTTPException(status_code=404, detail="Parcours not assigned to this class")
    access.is_active = False
    db.commit()
    return {"ok": True, "action": "removed"}


# ─── Teacher Class → Students ────────────────────────────────────────

@teacher_router.get("/students/search")
def search_students_for_class(
    q: str = Query("", min_length=0, max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Search for students within the teacher's school by name or email.

    Returns up to 20 matching students that are not already enrolled
    in the specified class (if class_id is provided).
    """
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="No school associated with your account")

    query = db.query(User).filter(
        User.role == "student",
        User.school_id == current_user.school_id,
        User.is_active == True,
    )
    if q.strip():
        like_q = f"%{q.strip()}%"
        query = query.filter(
            (User.full_name.ilike(like_q)) | (User.email.ilike(like_q))
        )
    students = query.order_by(User.full_name).limit(20).all()

    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "email": s.email,
            "niveau_scolaire": s.niveau_scolaire,
        }
        for s in students
    ]


@teacher_router.get("/classes/{class_id}/students", response_model=List[StudentEnrollmentRead])
def list_class_students(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: list students enrolled in a class."""
    _own_class_or_403(db, class_id, current_user.id)
    enrolls = db.query(StudentEnrollment).filter(
        StudentEnrollment.class_id == class_id,
        StudentEnrollment.is_active == True,
    ).all()
    result = []
    for e in enrolls:
        student = db.query(User).filter(User.id == e.student_id).first()
        result.append({
            "id": e.id,
            "student_id": e.student_id,
            "class_id": e.class_id,
            "student_name": student.full_name if student else None,
            "student_email": student.email if student else None,
            "enrolled_at": e.enrolled_at,
            "is_active": e.is_active,
        })
    return result


class EnrollStudentRequest(BaseModel):
    student_id: int


@teacher_router.post("/classes/{class_id}/students", response_model=StudentEnrollmentRead)
def enroll_student_in_class(
    class_id: int,
    body: EnrollStudentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: enroll a student in a class."""
    _own_class_or_403(db, class_id, current_user.id)
    student = db.query(User).filter(User.id == body.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    # School isolation: student must belong to the same school
    if student.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Student does not belong to your school")
    existing = db.query(StudentEnrollment).filter(
        StudentEnrollment.class_id == class_id,
        StudentEnrollment.student_id == body.student_id,
    ).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
        student_name = student.full_name if student else None
        student_email = student.email if student else None
        return {
            "id": existing.id,
            "student_id": existing.student_id,
            "class_id": existing.class_id,
            "student_name": student_name,
            "student_email": student_email,
            "enrolled_at": existing.enrolled_at,
            "is_active": existing.is_active,
        }
    enroll = StudentEnrollment(
        class_id=class_id,
        student_id=body.student_id,
    )
    db.add(enroll)
    db.commit()
    db.refresh(enroll)
    student_name = student.full_name if student else None
    student_email = student.email if student else None
    return {
        "id": enroll.id,
        "student_id": enroll.student_id,
        "class_id": enroll.class_id,
        "student_name": student_name,
        "student_email": student_email,
        "enrolled_at": enroll.enrolled_at,
        "is_active": enroll.is_active,
    }


@teacher_router.delete("/classes/{class_id}/students/{student_id}")
def remove_student_from_class(
    class_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: remove a student from a class."""
    _own_class_or_403(db, class_id, current_user.id)
    enroll = db.query(StudentEnrollment).filter(
        StudentEnrollment.class_id == class_id,
        StudentEnrollment.student_id == student_id,
    ).first()
    if not enroll:
        raise HTTPException(status_code=404, detail="Student not enrolled in this class")
    enroll.is_active = False
    db.commit()
    return {"ok": True, "action": "removed"}


# ─── Teacher Class → Messaging ───────────────────────────────────────

class ClassMessageRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    student_id: Optional[int] = None


@teacher_router.post("/classes/{class_id}/message")
def send_class_message(
    class_id: int,
    body: ClassMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: send a message to all active students of one of my classes,
    or to a single targeted student of that class."""
    tc = _own_class_or_403(db, class_id, current_user.id)
    if not tc.school_id:
        raise HTTPException(status_code=400, detail="Class has no school attached")

    subject = body.subject.strip()
    message_body = body.body.strip()
    if not subject or not message_body:
        raise HTTPException(status_code=422, detail="Subject and body must not be empty")

    if body.student_id is not None:
        enrolled = db.query(StudentEnrollment).filter(
            StudentEnrollment.class_id == class_id,
            StudentEnrollment.student_id == body.student_id,
            StudentEnrollment.is_active == True,
        ).first()
        if not enrolled:
            raise HTTPException(status_code=404, detail="Student not enrolled in this class")
        recipient_ids = [body.student_id]
    else:
        enrollments = db.query(StudentEnrollment).filter(
            StudentEnrollment.class_id == class_id,
            StudentEnrollment.is_active == True,
        ).all()
        recipient_ids = [e.student_id for e in enrollments]
        if not recipient_ids:
            raise HTTPException(status_code=400, detail="No active students in this class")

    messages = [
        Message(
            school_id=tc.school_id,
            sender_id=current_user.id,
            receiver_id=sid,
            type=MessageType.DIRECT,
            subject=subject,
            body=message_body,
            target_audience="students",
        )
        for sid in recipient_ids
    ]
    db.add_all(messages)
    db.commit()

    return {
        "ok": True,
        "class_id": class_id,
        "sent": len(messages),
        "student_ids": recipient_ids,
        "targeted_only": body.student_id is not None,
    }


TIER_ORDER = {"Gratuit": 0, "Basic": 1, "Silver": 2, "Golden": 3}


@teacher_router.get("/classes/{class_id}/students/progress")
def get_class_students_progress(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_teacher),
):
    """Teacher: get enriched student progress data for a class, including ABAC pack status."""
    _own_class_or_403(db, class_id, current_user.id)

    # 1. Get courses assigned to this class
    class_courses = db.query(ClassCourseAccess).filter(
        ClassCourseAccess.class_id == class_id,
        ClassCourseAccess.is_active == True,
    ).all()
    course_ids = [cca.course_id for cca in class_courses]

    # 2. Get active students in this class
    enrollments = db.query(StudentEnrollment).filter(
        StudentEnrollment.class_id == class_id,
        StudentEnrollment.is_active == True,
    ).all()
    student_ids = [e.student_id for e in enrollments]

    if not student_ids:
        return []

    # 3. Bulk-fetch course enrollments for these students + courses
    course_enrollments = []
    if course_ids and student_ids:
        course_enrollments = db.query(CourseEnrollment).filter(
            CourseEnrollment.student_id.in_(student_ids),
            CourseEnrollment.course_id.in_(course_ids),
        ).all()

    # Build lookup: student_id → list of progress_percent
    student_progress = {}
    for ce in course_enrollments:
        student_progress.setdefault(ce.student_id, []).append(ce.progress_percent or 0)

    # 4. Bulk-fetch quiz attempts for these students via quizzes in the class's courses
    # Quiz → Lesson → Module → course_id
    quiz_ids = []
    if course_ids:
        quizzes = db.query(Quiz.id).join(Lesson, Quiz.lesson_id == Lesson.id).join(
            Module, Lesson.module_id == Module.id
        ).filter(Module.course_id.in_(course_ids)).all()
        quiz_ids = [q[0] for q in quizzes]

    last_quiz = {}
    if quiz_ids and student_ids:
        attempts = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id.in_(quiz_ids),
            QuizAttempt.student_id.in_(student_ids),
            QuizAttempt.status == "completed",
        ).order_by(QuizAttempt.completed_at.desc()).all()
        for a in attempts:
            if a.student_id not in last_quiz:
                last_quiz[a.student_id] = {
                    "score_percent": a.score_percent,
                    "passed": a.passed,
                    "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                }

    # 5. Bulk-fetch active abonnements (packs) for students
    student_pack = {}
    if student_ids:
        now = datetime.now(timezone.utc)
        active_abos = db.query(Abonnement).filter(
            Abonnement.user_id.in_(student_ids),
            Abonnement.statut == "actif",
            Abonnement.fin > now,
        ).all()
        for abo in active_abos:
            pack = db.query(PackDefinition).filter(PackDefinition.id == abo.pack_id).first()
            if pack:
                student_pack[abo.user_id] = {
                    "tier": pack.tier,
                    "nom": pack.nom,
                    "fin": abo.fin.isoformat() if abo.fin else None,
                }

    # 6. Check for expired abonnements
    if student_ids:
        now = datetime.now(timezone.utc)
        expired_abos = db.query(Abonnement).filter(
            Abonnement.user_id.in_(student_ids),
            Abonnement.fin <= now,
        ).order_by(Abonnement.fin.desc()).all()
        for abo in expired_abos:
            if abo.user_id not in student_pack:
                pack = db.query(PackDefinition).filter(PackDefinition.id == abo.pack_id).first()
                student_pack[abo.user_id] = {
                    "tier": pack.tier if pack else None,
                    "nom": pack.nom if pack else None,
                    "fin": abo.fin.isoformat() if abo.fin else None,
                    "expired": True,
                }

    # 7. Build response
    result = []
    for enroll in enrollments:
        student = db.query(User).filter(User.id == enroll.student_id).first()
        progresses = student_progress.get(enroll.student_id, [])
        avg_progress = round(sum(progresses) / len(progresses)) if progresses else 0
        quiz_data = last_quiz.get(enroll.student_id)
        pack_data = student_pack.get(enroll.student_id)

        # Determine ABAC blocking status
        pack_status = "ok"
        pack_label = ""
        pack_expired = False
        if pack_data:
            pack_expired = pack_data.get("expired", False)
            tier = pack_data.get("tier", "Gratuit")
            pack_label = pack_data.get("nom", tier)
            if pack_expired:
                pack_status = "expired"
            elif tier == "Gratuit" and avg_progress >= 80:
                pack_status = "quota_exceeded"
        else:
            pack_status = "none"
            pack_label = "Aucun pack"

        # Courses enrolled count
        enrolled_courses_count = len(progresses)

        result.append({
            "student_id": enroll.student_id,
            "student_name": student.full_name if student else None,
            "student_email": student.email if student else None,
            "progress_percent": avg_progress,
            "courses_enrolled": enrolled_courses_count,
            "total_class_courses": len(course_ids),
            "last_quiz_score": quiz_data["score_percent"] if quiz_data else None,
            "last_quiz_passed": quiz_data["passed"] if quiz_data else None,
            "last_quiz_at": quiz_data["completed_at"] if quiz_data else None,
            "pack_tier": pack_data["tier"] if pack_data else None,
            "pack_label": pack_label,
            "pack_status": pack_status,
            "pack_expiry": pack_data["fin"] if pack_data else None,
        })

    result.sort(key=lambda s: s["student_name"] or "")
    return result


# ═══════════════════════════════════════════════════════════════════════
# SUPER ADMIN CATALOG ENDPOINTS  (/api/admin/teacher-classes...)
# ═══════════════════════════════════════════════════════════════════════

@admin_teacher_router.get("/teacher-classes", response_model=List[TeacherClassRead])
def admin_list_all_teacher_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_super_admin_for_teacher),
    school_id: Optional[int] = Query(None, description="Filter by school"),
    search: Optional[str] = Query(None, description="Search by class name or teacher name"),
):
    """Super Admin: list all teacher classes across all schools."""
    q = db.query(TeacherClass)
    if school_id:
        q = q.filter(TeacherClass.school_id == school_id)
    if search:
        q = q.join(User, TeacherClass.teacher_id == User.id).filter(
            TeacherClass.name.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        )
    classes = q.order_by(TeacherClass.created_at.desc()).all()
    return [_serialize_tc(tc, db) for tc in classes]


@admin_teacher_router.get("/teacher-classes/{class_id}", response_model=TeacherClassRead)
def admin_get_teacher_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_super_admin_for_teacher),
):
    """Super Admin: get details of any teacher class."""
    tc = db.query(TeacherClass).filter(TeacherClass.id == class_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Teacher class not found")
    return _serialize_tc(tc, db)


@admin_teacher_router.get("/teacher-classes/{class_id}/courses", response_model=List[ClassCourseAccessRead])
def admin_list_teacher_class_courses(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_super_admin_for_teacher),
):
    """Super Admin: list courses assigned to a teacher class."""
    tc = db.query(TeacherClass).filter(TeacherClass.id == class_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Teacher class not found")
    accesses = db.query(ClassCourseAccess).filter(
        ClassCourseAccess.class_id == class_id,
        ClassCourseAccess.is_active == True,
    ).all()
    result = []
    for a in accesses:
        course = db.query(Course).filter(Course.id == a.course_id).first()
        result.append({
            "id": a.id,
            "class_id": a.class_id,
            "course_id": a.course_id,
            "course_title": course.title if course else None,
            "assigned_at": a.assigned_at,
            "is_active": a.is_active,
        })
    return result


@admin_teacher_router.get("/teacher-classes/{class_id}/students", response_model=List[StudentEnrollmentRead])
def admin_list_teacher_class_students(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_super_admin_for_teacher),
):
    """Super Admin: list students enrolled in a teacher class."""
    tc = db.query(TeacherClass).filter(TeacherClass.id == class_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Teacher class not found")
    enrolls = db.query(StudentEnrollment).filter(
        StudentEnrollment.class_id == class_id,
        StudentEnrollment.is_active == True,
    ).all()
    result = []
    for e in enrolls:
        student = db.query(User).filter(User.id == e.student_id).first()
        result.append({
            "id": e.id,
            "student_id": e.student_id,
            "class_id": e.class_id,
            "student_name": student.full_name if student else None,
            "student_email": student.email if student else None,
            "enrolled_at": e.enrolled_at,
            "is_active": e.is_active,
        })
    return result


@admin_teacher_router.get("/teacher-courses/catalog")
def admin_teacher_courses_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_super_admin_for_teacher),
    school_id: Optional[int] = Query(None, description="Filter by school"),
    teacher_id: Optional[int] = Query(None, description="Filter by teacher"),
    search: Optional[str] = Query(None, description="Search by course title or teacher name"),
):
    """Super Admin: catalog view of all teacher-owned courses with class/student info."""
    q = db.query(TeacherClass)
    if school_id:
        q = q.filter(TeacherClass.school_id == school_id)
    if teacher_id:
        q = q.filter(TeacherClass.teacher_id == teacher_id)
    if search:
        q = q.join(User, TeacherClass.teacher_id == User.id).filter(
            TeacherClass.name.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        )
    classes = q.order_by(TeacherClass.created_at.desc()).all()

    result = []
    for tc in classes:
        courses = []
        accesses = db.query(ClassCourseAccess).filter(
            ClassCourseAccess.class_id == tc.id,
            ClassCourseAccess.is_active == True,
        ).all()
        for a in accesses:
            course = db.query(Course).filter(Course.id == a.course_id).first()
            if course:
                courses.append({
                    "course_id": course.id,
                    "title": course.title,
                    "category": course.category,
                    "level": course.level,
                    "status": course.status,
                    "is_published": course.is_published,
                })
        students_count = db.query(func.count(StudentEnrollment.id)).filter(
            StudentEnrollment.class_id == tc.id,
            StudentEnrollment.is_active == True,
        ).scalar() or 0
        teacher = db.query(User).filter(User.id == tc.teacher_id).first()
        school = db.query(School).filter(School.id == tc.school_id).first() if tc.school_id else None
        result.append({
            "class_id": tc.id,
            "class_name": tc.name,
            "class_code": tc.code,
            "teacher_id": tc.teacher_id,
            "teacher_name": teacher.full_name if teacher else None,
            "teacher_email": teacher.email if teacher else None,
            "school_id": tc.school_id,
            "school_name": school.name if school else None,
            "courses": courses,
            "students_count": students_count,
            "created_at": tc.created_at.isoformat() if tc.created_at else None,
        })

    return {
        "total_classes": len(result),
        "classes": result,
    }
