"""
Routers pour le admin_pédagogique (portée école).
Endpoints:
  - GET  /pedagogical-lead/progress-report
  - PUT  /pedagogical-lead/courses/{id}/review-local
  - POST /pedagogical-lead/escalate/{course_id}
  - POST /pedagogical-lead/classes/{id}/reassign-teacher
  - PUT  /pedagogical-lead/assignments/{id}/postpone
  - GET  /pedagogical-lead/performance
  - GET  /pedagogical-lead/ai-questions-analysis
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_pedagogical_lead, check_school_access
from app.models import (
    Course, User, ClassRoom, Assignment, ClassroomEnrollment,
    LessonProgress, PedagogicalEscalation, TeacherReassignment,
)
from app.auth import get_current_user
from app.services.course_lifecycle import can_transition_status

router = APIRouter(prefix="/pedagogical-lead", tags=["Pedagogical (School)"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CoursePendingRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    school_id: Optional[int] = None
    author_id: Optional[int] = None
    pedagogical_status: Optional[str] = None
    created_at: Optional[str] = None
    author_name: Optional[str] = None

class LocalReviewRequest(BaseModel):
    action: str  # approved_local, needs_revision, escalate
    comment: Optional[str] = None


class EscalateRequest(BaseModel):
    reason: str
    details: Optional[str] = None


class ReassignTeacherRequest(BaseModel):
    new_teacher_id: int
    start_date: str  # ISO datetime
    end_date: Optional[str] = None
    reason: Optional[str] = None


class PostponeRequest(BaseModel):
    new_date: Optional[str] = None  # ISO datetime, null = validate replacement
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# 8. Suivi de progression et validation locale
# ---------------------------------------------------------------------------

@router.get("/progress-report")
def progress_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_lead),
):
    """Avancement réel vs calendrier officiel, par classe/matière, scoped à l'école."""
    school_id = current_user.school_id
    classrooms = db.query(ClassRoom).filter(ClassRoom.school_id == school_id).all()
    report = []
    for cls in classrooms:
        enrolled = db.query(func.count(ClassroomEnrollment.id)).filter(
            ClassroomEnrollment.classroom_id == cls.id
        ).scalar() or 0
        completed = db.query(func.count(LessonProgress.id)).filter(
            LessonProgress.status == "completed",
        ).join(ClassroomEnrollment, ClassroomEnrollment.id == LessonProgress.enrollment_id).filter(
            ClassroomEnrollment.classroom_id == cls.id
        ).scalar() or 0
        report.append({
            "classroom_id": cls.id,
            "name": cls.name,
            "enrolled_students": enrolled,
            "completed_lessons": completed,
        })
    return {"school_id": school_id, "classrooms": report}


@router.get("/courses/pending")
def courses_pending(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_lead),
):
    """Liste les cours de l'école en attente de revue pédagogique locale."""
    school_id = current_user.school_id
    q = db.query(Course).filter(
        Course.school_id == school_id,
        Course.pedagogical_status.in_(["pending_review", "needs_revision"]),
    )
    total = q.count()
    courses = q.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for c in courses:
        author = db.query(User).filter(User.id == c.author_id).first() if c.author_id else None
        result.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "school_id": c.school_id,
            "author_id": c.author_id,
            "pedagogical_status": c.pedagogical_status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "author_name": author.full_name if author else None,
        })

    return {"total": total, "skip": skip, "limit": limit, "courses": result}


@router.put("/courses/{course_id}/review-local")
def review_local(
    course_id: int,
    body: LocalReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_lead),
):
    """Approuve en 'approved_local' (jamais 'approved_for_b2b'), ou escalade."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    check_school_access(current_user, course.school_id)

    if body.action == "escalate":
        esc = PedagogicalEscalation(
            course_id=course_id,
            escalated_by=current_user.id,
            school_id=current_user.school_id,
            reason=body.comment or "Escalade par pedagogical_lead",
            details=body.details,
        )
        db.add(esc)
        db.commit()
        db.refresh(esc)
        return {"escalation_id": esc.id, "status": "escalated"}

    valid_actions = {"approved_local", "needs_revision"}
    if body.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")

    can_transition_status(course, body.action, current_user)

    course.pedagogical_status = body.action
    course.validated_by = current_user.id
    course.validated_at = datetime.now(timezone.utc)
    course.validated_by_role = "pedagogical_lead"
    db.commit()
    db.refresh(course)
    return {"id": course.id, "pedagogical_status": course.pedagogical_status}


@router.post("/escalate/{course_id}")
def escalate_course(
    course_id: int,
    body: EscalateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_lead),
):
    """Crée une entrée dans la file d'escalade."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    check_school_access(current_user, course.school_id)

    esc = PedagogicalEscalation(
        course_id=course_id,
        escalated_by=current_user.id,
        school_id=current_user.school_id,
        reason=body.reason,
        details=body.details,
    )
    db.add(esc)
    db.commit()
    db.refresh(esc)
    return {"id": esc.id, "status": "pending"}


# ---------------------------------------------------------------------------
# 9. Continuité pédagogique
# ---------------------------------------------------------------------------

@router.post("/classes/{class_id}/reassign-teacher")
def reassign_teacher(
    class_id: int,
    body: ReassignTeacherRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_lead),
):
    """Réaffectation temporaire d'une classe à un autre enseignant de la MÊME école."""
    classroom = db.query(ClassRoom).filter(ClassRoom.id == class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    check_school_access(current_user, classroom.school_id)

    new_teacher = db.query(User).filter(
        User.id == body.new_teacher_id,
        User.role == "teacher",
        User.school_id == current_user.school_id,
    ).first()
    if not new_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found in this school")

    reassignment = TeacherReassignment(
        class_id=class_id,
        original_teacher_id=classroom.teacher_id,
        new_teacher_id=body.new_teacher_id,
        school_id=current_user.school_id,
        start_date=datetime.fromisoformat(body.start_date),
        end_date=datetime.fromisoformat(body.end_date) if body.end_date else None,
        reason=body.reason,
        created_by=current_user.id,
    )
    db.add(reassignment)
    db.commit()
    db.refresh(reassignment)
    return {"id": reassignment.id, "status": "created"}


@router.put("/assignments/{assignment_id}/postpone")
def postpone_assignment(
    assignment_id: int,
    body: PostponeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_lead),
):
    """Report ou validation d'un remplacement encadré pour une évaluation."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    check_school_access(current_user, assignment.school_id)

    if body.new_date:
        assignment.due_date = datetime.fromisoformat(body.new_date)
    assignment.description = (assignment.description or "") + f"\n[Remplacement] {body.reason or 'Reporté par admin pédagogique'}"
    db.commit()
    return {"id": assignment.id, "status": "updated"}


# ---------------------------------------------------------------------------
# 10. Dashboard de performance locale
# ---------------------------------------------------------------------------

@router.get("/performance")
def performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_lead),
):
    """Résultats agrégés par classe de l'école."""
    school_id = current_user.school_id
    classrooms = db.query(ClassRoom).filter(ClassRoom.school_id == school_id).all()
    performance_data = []
    for cls in classrooms:
        enrolled = db.query(func.count(ClassroomEnrollment.id)).filter(
            ClassroomEnrollment.classroom_id == cls.id
        ).scalar() or 0
        completed = db.query(func.count(LessonProgress.id)).filter(
            LessonProgress.status == "completed",
        ).join(ClassroomEnrollment, ClassroomEnrollment.id == LessonProgress.enrollment_id).filter(
            ClassroomEnrollment.classroom_id == cls.id
        ).scalar() or 0
        performance_data.append({
            "classroom_id": cls.id,
            "name": cls.name,
            "enrolled": enrolled,
            "lessons_completed": completed,
            "completion_rate": round(completed / max(enrolled, 1) * 100, 1),
        })
    return {"school_id": school_id, "performance": performance_data}


@router.get("/ai-questions-analysis")
def ai_questions_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_lead),
):
    """Analyse des questions récurrentes posées à l'AI Tutor par les élèves de l'école."""
    from app.models_ai_conversations import AIChatMessage, AIConversation
    school_id = current_user.school_id

    messages = (
        db.query(AIChatMessage.content, func.count(AIChatMessage.id).label("count"))
        .join(AIConversation, AIConversation.id == AIChatMessage.conversation_id)
        .filter(
            AIConversation.school_id == school_id,
            AIChatMessage.role == "user",
        )
        .group_by(AIChatMessage.content)
        .order_by(func.count(AIChatMessage.id).desc())
        .limit(20)
        .all()
    )
    return {
        "school_id": school_id,
        "top_questions": [{"content": m[0][:200], "count": m[1]} for m in messages],
    }
