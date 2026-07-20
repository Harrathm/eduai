from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional, List

from app.db import get_db
from app.auth import get_current_user
from app.models import User, TeacherClass, ClassCourseAccess, StudentEnrollment, Course, School
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
        "students_count": students_count,
    }


# ═══════════════════════════════════════════════════════════════════════
# TEACHER-FACING ENDPOINTS  (/api/teacher/classes)
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


# ─── Teacher Class → Students ────────────────────────────────────────

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
