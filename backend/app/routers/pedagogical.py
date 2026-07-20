"""
Routers pour le super_admin_pédagogique (portée plateforme).
Endpoints:
  - GET  /pedagogical/courses/pending
  - PUT  /pedagogical/courses/{id}/review
  - GET  /pedagogical/reports/curriculum-coverage
  - GET  /pedagogical/reports
  - PUT  /pedagogical/reports/{id}/resolve
  - GET  /pedagogical/escalations
  - PUT  /pedagogical/escalations/{id}/resolve
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_pedagogical_admin
from app.models import (
    Course, User, School, AIContentReport, PedagogicalEscalation, ClassRoom,
    LessonProgress, Enrollment,
)
from app.auth import get_current_user
from app.services.course_lifecycle import can_transition_status

router = APIRouter(prefix="/pedagogical", tags=["Pedagogical (Platform)"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CourseReviewRequest(BaseModel):
    action: str  # approved_for_b2b, needs_revision
    comment: Optional[str] = None


class ReportResolveRequest(BaseModel):
    action: str  # resolved, dismissed
    response: str


class EscalationResolveRequest(BaseModel):
    resolution: str


# ---------------------------------------------------------------------------
# 5. File de validation et décisions
# ---------------------------------------------------------------------------

@router.get("/courses/pending")
def list_pending_courses(
    school_id: Optional[int] = None,
    level: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Liste des cours en attente de review, toutes écoles confondues."""
    q = db.query(Course).filter(Course.pedagogical_status.in_(["pending_review", "needs_revision"]))
    if school_id:
        q = q.filter(Course.school_id == school_id)
    if level:
        q = q.filter(Course.level == level)
    if category:
        q = q.filter(Course.category == category)
    total = q.count()
    courses = q.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "school_id": c.school_id,
                "level": c.level,
                "category": c.category,
                "pedagogical_status": c.pedagogical_status,
                "author_id": c.author_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in courses
        ],
    }


@router.put("/courses/{course_id}/review")
def review_course(
    course_id: int,
    body: CourseReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Approuve ou demande correction pour un cours. Seul pedagogical_admin peut approuver pour B2B."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    valid_actions = {"approved_for_b2b", "needs_revision"}
    if body.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")

    can_transition_status(course, body.action, current_user)

    course.pedagogical_status = body.action
    course.validated_by = current_user.id
    course.validated_at = datetime.now(timezone.utc)
    course.validated_by_role = "pedagogical_admin"
    db.commit()
    db.refresh(course)
    return {"id": course.id, "pedagogical_status": course.pedagogical_status}


@router.get("/reports/curriculum-coverage")
def curriculum_coverage(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Rapport de couverture curriculaire (matières/niveaux mal couverts)."""
    results = (
        db.query(
            Course.category,
            Course.level,
            func.count(Course.id).label("course_count"),
            func.count(func.distinct(Course.school_id)).label("school_count"),
        )
        .filter(Course.pedagogical_status.in_(["approved_local", "approved_for_b2b"]))
        .group_by(Course.category, Course.level)
        .order_by(func.count(Course.id).asc())
        .all()
    )
    return {
        "coverage": [
            {
                "category": r[0] or "Non défini",
                "level": r[1] or "Non défini",
                "course_count": r[2],
                "school_count": r[3],
            }
            for r in results
        ]
    }


# ---------------------------------------------------------------------------
# 6. Gestion des signalements de contenu IA
# ---------------------------------------------------------------------------

@router.post("/ai/reports")
def create_ai_report(
    message_id: Optional[str] = None,
    conversation_id: Optional[int] = None,
    reason: str = Query(...),
    details: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tout utilisateur authentifié peut signaler une réponse IA incorrecte."""
    report = AIContentReport(
        message_id=message_id,
        conversation_id=conversation_id,
        reported_by=current_user.id,
        school_id=getattr(current_user, "school_id", None),
        reason=reason,
        details=details,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "status": report.status}


@router.get("/reports")
def list_reports(
    status: Optional[str] = "pending",
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Liste des signalements de contenu IA, toutes écoles."""
    q = db.query(AIContentReport)
    if status:
        q = q.filter(AIContentReport.status == status)
    total = q.count()
    reports = q.order_by(AIContentReport.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "reports": [
            {
                "id": r.id,
                "message_id": r.message_id,
                "reported_by": r.reported_by,
                "school_id": r.school_id,
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ],
    }


@router.put("/reports/{report_id}/resolve")
def resolve_report(
    report_id: int,
    body: ReportResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Clôture d'un signalement avec action prise."""
    report = db.query(AIContentReport).filter(AIContentReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = body.action
    report.resolved_by = current_user.id
    report.resolved_at = datetime.now(timezone.utc)
    report.resolution_action = body.action
    report.resolution_response = body.response
    db.commit()
    return {"id": report.id, "status": report.status}


# ---------------------------------------------------------------------------
# 7. Arbitrage des escalades
# ---------------------------------------------------------------------------

@router.get("/escalations")
def list_escalations(
    status: Optional[str] = "pending",
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Liste des cas escaladés par les pedagogical_lead."""
    q = db.query(PedagogicalEscalation)
    if status:
        q = q.filter(PedagogicalEscalation.status == status)
    total = q.count()
    escalations = q.order_by(PedagogicalEscalation.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "escalations": [
            {
                "id": e.id,
                "course_id": e.course_id,
                "escalated_by": e.escalated_by,
                "school_id": e.school_id,
                "reason": e.reason,
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in escalations
        ],
    }


@router.put("/escalations/{escalation_id}/resolve")
def resolve_escalation(
    escalation_id: int,
    body: EscalationResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Décision finale sur un cas escaladé."""
    esc = db.query(PedagogicalEscalation).filter(PedagogicalEscalation.id == escalation_id).first()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    esc.status = "resolved"
    esc.resolved_by = current_user.id
    esc.resolved_at = datetime.now(timezone.utc)
    esc.resolution = body.resolution
    db.commit()
    return {"id": esc.id, "status": esc.status}
