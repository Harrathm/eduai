"""
Routers pour le super_admin_pédagogique (portée plateforme).
Endpoints:
  - GET  /pedagogical/courses/pending
  - PUT  /pedagogical/courses/{id}/review
  - GET  /pedagogical/reports/curriculum-coverage
  - GET  /pedagogical/curriculum-coverage
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
    LessonProgress, Enrollment, Matiere, NiveauEtude, ChapterPathway, Notion,
    ContenuNotion,
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
# 5b. Couverture détaillée du programme (chapitre → notion)
# ---------------------------------------------------------------------------

def _strip_accents(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


@router.get("/curriculum-coverage")
def curriculum_coverage_detail(
    niveau_scolaire: Optional[str] = None,
    matiere: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Couverture détaillée du programme officiel : arbre Chapitre → Notion → is_covered."""
    from sqlalchemy.orm import joinedload

    q = db.query(Matiere).options(
        joinedload(Matiere.niveau_etude),
        joinedload(Matiere.chapitres).joinedload(ChapterPathway.notions).joinedload(Notion.contenus),
    )

    if niveau_scolaire:
        target = _strip_accents(niveau_scolaire.lower())
        niveaux = db.query(NiveauEtude).all()
        matched_ids = [n.id for n in niveaux if target in _strip_accents(n.nom.lower())]
        if matched_ids:
            q = q.filter(Matiere.niveau_etude_id.in_(matched_ids))

    if matiere:
        target = _strip_accents(matiere.lower())
        matieres = q.all()
        matieres = [m for m in matieres if target in _strip_accents(m.nom.lower())]
    else:
        matieres = q.all()

    results = []
    for m in matieres:
        chapitres_out = []
        for ch in sorted(m.chapitres, key=lambda c: c.ordre):
            notions_out = []
            for no in sorted(ch.notions, key=lambda n: n.ordre):
                published = [c for c in no.contenus if c.statut_pedagogique == "a"]
                notions_out.append({
                    "id": no.id,
                    "nom": no.nom,
                    "is_covered": len(published) > 0,
                    "contenus_count": len(no.contenus),
                    "published_count": len(published),
                })
            chapitres_out.append({
                "id": ch.id,
                "nom": ch.nom,
                "ordre": ch.ordre,
                "notions": notions_out,
                "total_notions": len(notions_out),
                "covered_notions": sum(1 for n in notions_out if n["is_covered"]),
            })
        total_notions = sum(ch["total_notions"] for ch in chapitres_out)
        covered = sum(ch["covered_notions"] for ch in chapitres_out)
        results.append({
            "niveau": m.niveau_etude.nom,
            "matiere": m.nom,
            "matiere_id": m.id,
            "chapitres": chapitres_out,
            "total_notions": total_notions,
            "covered_notions": covered,
            "coverage_pct": round(covered / total_notions * 100, 1) if total_notions else 0,
        })

    return {"niveau_scolaire": niveau_scolaire, "matiere": matiere, "matieres": results}

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


# ============================================================
# STUDY PACKS — CRUD (pedagogical_admin uniquement)
# ============================================================

@router.post("/packs")
def create_pack(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Créer un nouveau pack d'étude. Réservé au pedagogical_admin (plateforme)."""
    from app.models import StudyPack, PackStatus

    name = body.get("name")
    niveau_scolaire = body.get("niveau_scolaire")
    price = body.get("price")

    if not name or not niveau_scolaire or price is None:
        raise HTTPException(status_code=400, detail="name, niveau_scolaire et price sont requis")

    pack = StudyPack(
        name=name,
        description=body.get("description"),
        niveau_scolaire=niveau_scolaire,
        matieres=body.get("matieres"),
        price=price,
        currency=body.get("currency", "TND"),
        validity_duration_days=body.get("validity_duration_days", 365),
        status=PackStatus.DRAFT.value,
        created_by=current_user.id,
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)
    return {"id": pack.id, "name": pack.name, "status": pack.status, "message": "Pack créé (draft)"}


@router.put("/packs/{pack_id}")
def update_pack(
    pack_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Modifier un pack. Réservé au pedagogical_admin."""
    from app.models import StudyPack

    pack = db.query(StudyPack).filter(StudyPack.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    for field in ["name", "description", "niveau_scolaire", "matieres", "price", "currency", "validity_duration_days"]:
        if field in body:
            setattr(pack, field, body[field])

    db.commit()
    db.refresh(pack)
    return {"id": pack.id, "name": pack.name, "status": pack.status, "message": "Pack mis à jour"}


@router.put("/packs/{pack_id}/publish")
def publish_pack(
    pack_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Passer un pack de draft à published."""
    from app.models import StudyPack, PackStatus

    pack = db.query(StudyPack).filter(StudyPack.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    pack.status = PackStatus.PUBLISHED.value
    db.commit()
    return {"id": pack.id, "status": pack.status, "message": "Pack publié"}


@router.put("/packs/{pack_id}/archive")
def archive_pack(
    pack_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Archiver un pack."""
    from app.models import StudyPack, PackStatus

    pack = db.query(StudyPack).filter(StudyPack.id == pack_id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    pack.status = PackStatus.ARCHIVED.value
    db.commit()
    return {"id": pack.id, "status": pack.status, "message": "Pack archivé"}


@router.get("/packs")
def list_all_packs(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pedagogical_admin),
):
    """Liste tous les packs (tous statuts). Réservé au pedagogical_admin."""
    from app.models import StudyPack

    query = db.query(StudyPack)
    if status:
        query = query.filter(StudyPack.status == status)

    total = query.count()
    packs = query.order_by(StudyPack.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "niveau_scolaire": p.niveau_scolaire,
                "matieres": p.matieres,
                "price": p.price,
                "currency": p.currency,
                "validity_duration_days": p.validity_duration_days,
                "status": p.status,
                "created_by": p.created_by,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in packs
        ],
    }
