"""Courses API endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone

from app.db import get_db
from app.auth import get_current_user
from app.deps import set_tenant_context, check_school_access, require_teacher_or_admin, get_user_role
from app.models import User, Course, Module, Lesson, CourseEnrollment
from app.models import UserRole, CourseStatus, Transaction, TransactionType, Currency
from app.services.course_access import has_course_access

VALID_CATEGORY_CIBLE = {"Scolaire", "Soft_Skill", "Teacher_Training"}


def _validate_course_abac_fields(user: User, data, is_update: bool = False):
    """RBAC + ABAC field validation for teacher-facing course endpoints."""
    role = get_user_role(user)
    category_cible = getattr(data, "category_cible", None)

    if role == "teacher" and category_cible and category_cible != "Scolaire":
        raise HTTPException(
            status_code=403,
            detail="Les enseignants ne peuvent créer que des cours de type 'Scolaire'.",
        )

    if category_cible and category_cible not in VALID_CATEGORY_CIBLE:
        raise HTTPException(
            status_code=400,
            detail=f"category_cible invalide : '{category_cible}'. Valeurs autorisées : {', '.join(sorted(VALID_CATEGORY_CIBLE))}",
        )

    if category_cible == "Scolaire":
        niveau = getattr(data, "niveau_scolaire", None)
        cat = getattr(data, "category", None)
        missing = []
        if not niveau:
            missing.append("niveau_scolaire")
        if not cat:
            missing.append("category (matière)")
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Pour un cours de type 'Scolaire', les champs suivants sont obligatoires : {', '.join(missing)}.",
            )
from app.schemas import (
    CourseRead,
    CourseCreate,
    CourseUpdate,
    ModuleCreate,
    ModuleUpdate,
    LessonCreate,
    LessonUpdate,
    EnrollmentRead,
)

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
def list_courses(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """List all published courses (students can view)"""
    query = db.query(Course).filter(Course.school_id == current_user.school_id)
    
    if status:
        query = query.filter(Course.status == status)
    else:
        query = query.filter(Course.status == CourseStatus.PUBLISHED)
    
    total = query.count()
    items = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/my-courses")
def my_courses(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """Get courses created by current teacher"""
    query = db.query(Course).filter(Course.author_id == current_user.id)
    total = query.count()
    items = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/my-sales")
def my_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Retourne les ventes de l'enseignant indépendant connecté (uniquement ses propres cours)."""
    from app.models import CoursePurchase

    # Récupérer les cours de cet enseignant
    my_courses = db.query(Course).filter(
        Course.owner_type == "independent_teacher",
        Course.owner_id == current_user.id,
    ).all()
    my_course_ids = [c.id for c in my_courses]

    if not my_course_ids:
        return {"total_sales": 0, "total_revenue": 0, "sales": []}

    purchases = db.query(CoursePurchase).filter(
        CoursePurchase.course_id.in_(my_course_ids)
    ).order_by(CoursePurchase.purchased_at.desc()).all()

    total_revenue = sum(p.teacher_revenue for p in purchases)
    return {
        "total_sales": len(purchases),
        "total_revenue": total_revenue,
        "sales": [
            {
                "id": p.id,
                "course_id": p.course_id,
                "amount_paid": p.amount_paid,
                "platform_fee": p.platform_fee,
                "teacher_revenue": p.teacher_revenue,
                "purchased_at": p.purchased_at.isoformat() if p.purchased_at else None,
            }
            for p in purchases
        ],
    }


@router.get("/{course_id}", response_model=CourseRead)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Get course by ID — checks pack access for students."""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    role = get_user_role(current_user)
    # Students must have pack-based access
    if role in ("STUDENT", "USER"):
        if not has_course_access(current_user, course, db):
            tag = getattr(course, "tag_pack_requis", "Basic") or "Basic"
            raise HTTPException(
                status_code=402,
                detail=f"Accès requis : ce cours nécessite un abonnement {tag}. "
                       f"Veuillez souscrire à un pack pour y accéder.",
            )
    
    return course


@router.post("", response_model=CourseRead)
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """Create a new course (teachers and admins only)"""
    _validate_course_abac_fields(current_user, course_in)

    course = Course(
        **course_in.model_dump(),
        school_id=current_user.school_id,
        author_id=current_user.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return course


def _can_write_course(user: User, course: Course) -> bool:
    role = get_user_role(user)
    if role in ("super_admin", "pedagogical_admin"):
        return True
    if role == "teacher":
        return course.author_id == user.id
    return course.school_id == user.school_id


@router.put("/{course_id}", response_model=CourseRead)
def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """Update course (author or admin only)"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if not _can_write_course(current_user, course):
        raise HTTPException(status_code=403, detail="Seul l'auteur du cours ou un administrateur peut le modifier")

    check_school_access(current_user, course.school_id)

    _validate_course_abac_fields(current_user, course_update, is_update=True)
    
    if course_update.title is not None:
        course.title = course_update.title
    if course_update.description is not None:
        course.description = course_update.description
    if course_update.price_tokens is not None:
        course.price_tokens = course_update.price_tokens
    if course_update.price_dt is not None:
        course.price_dt = course_update.price_dt
    if course_update.status is not None:
        course.status = course_update.status
    if course_update.category_cible is not None:
        course.category_cible = course_update.category_cible
    if course_update.niveau_scolaire is not None:
        course.niveau_scolaire = course_update.niveau_scolaire
    if course_update.tag_pack_requis is not None:
        course.tag_pack_requis = course_update.tag_pack_requis
    
    db.commit()
    db.refresh(course)
    
    return course


@router.post("/{course_id}/enroll", response_model=EnrollmentRead)
def enroll_student(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Enroll student in course — free courses only. Paid courses use /purchase endpoint."""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.status != CourseStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Course not available")

    is_paid = course.price and course.price > 0
    if is_paid:
        raise HTTPException(
            status_code=400,
            detail="Cours payant — utilisez l'endpoint /purchase pour acheter le cours"
        )
    
    # Check if already enrolled
    existing = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id,
        CourseEnrollment.student_id == current_user.id,
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled")
    
    enrollment = CourseEnrollment(
        course_id=course_id,
        student_id=current_user.id,
        enrolled_at=datetime.now(timezone.utc),
    )
    db.add(enrollment)
    db.commit()
    
    return enrollment


@router.get("/{course_id}/enrollments")
def list_enrollments(
    course_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """List students enrolled in course"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    query = db.query(CourseEnrollment).filter(CourseEnrollment.course_id == course_id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


# ---- Modules ----

@router.post("/{course_id}/modules", response_model=ModuleCreate)
def create_module(
    course_id: int,
    module_in: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """Create module in course"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if not _can_write_course(current_user, course):
        raise HTTPException(status_code=403, detail="Seul l'auteur du cours ou un administrateur peut le modifier")

    module = Module(
        **module_in.model_dump(),
        course_id=course_id,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    
    return module


# ---- Lessons ----

@router.post("/modules/{module_id}/lessons", response_model=LessonCreate)
def create_lesson(
    module_id: int,
    lesson_in: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """Create lesson in module"""
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    course = db.query(Course).filter(
        Course.id == module.course_id,
        Course.school_id == current_user.school_id,
    ).first()

    if not course:
        raise HTTPException(status_code=404, detail="Module not found in your school")

    if not _can_write_course(current_user, course):
        raise HTTPException(status_code=403, detail="Seul l'auteur du cours ou un administrateur peut le modifier")

    lesson = Lesson(
        **lesson_in.model_dump(),
        module_id=module_id,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    return lesson


# ---------------------------------------------------------------------------
# 5. Fixation de prix (enseignant indépendant)
# ---------------------------------------------------------------------------

@router.put("/{course_id}/price")
def set_course_price(
    course_id: int,
    price: float = Query(..., ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Fixe le prix d'un cours. Uniquement pour owner_type='independent_teacher' ET owner_id=currentUser."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.owner_type != "independent_teacher":
        raise HTTPException(status_code=403, detail="Seuls les cours d'enseignants indépendants ont un prix configurable")
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez fixer le prix que pour vos propres cours")

    from app.core.config import get_settings
    settings = get_settings()
    if price > settings.max_independent_course_price:
        raise HTTPException(
            status_code=400,
            detail=f"Le prix ne peut pas dépasser {settings.max_independent_course_price} TND"
        )

    course.price = price
    db.commit()
    db.refresh(course)
    return {"id": course.id, "price": course.price, "currency": course.currency}


# ---------------------------------------------------------------------------
# 6. Achat d'un cours payant
# ---------------------------------------------------------------------------

@router.post("/{course_id}/purchase")
def purchase_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """Achète un cours payant avec débit réel du solde DT."""
    from app.models import CoursePurchase

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if not course.price or course.price <= 0:
        raise HTTPException(status_code=400, detail="Ce cours est gratuit, pas besoin d'acheter")

    # Vérifier si déjà acheté
    existing = db.query(CoursePurchase).filter(
        CoursePurchase.student_id == current_user.id,
        CoursePurchase.course_id == course_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vous avez déjà acheté ce cours")

    # Vérifier le solde DT
    from app.services.wallet import get_dt_balance, debit_dt, InsufficientCreditsError
    current_dt = get_dt_balance(db, current_user.id)
    if current_dt < course.price:
        raise HTTPException(
            status_code=402,
            detail=f"Solde insuffisant. Solde actuel: {current_dt} {course.currency or 'TND'}, prix du cours: {course.price} {course.currency or 'TND'}"
        )

    # Débiter le solde DT via WalletTransaction (append-only audit trail)
    # commit=False : tout sera commité ensemble à la ligne 383
    try:
        debit_dt(db, current_user.id, course.price, source="purchase", reason=f"Achat cours: {course.title}", commit=False)
    except InsufficientCreditsError:
        raise HTTPException(status_code=402, detail="Solde insuffisant lors du débit")

    # Créer la transaction financière
    transaction_school = current_user.school_id or course.school_id
    if not transaction_school:
        raise HTTPException(status_code=400, detail="Aucun établissement associé")

    transaction = Transaction(
        school_id=transaction_school,
        user_id=current_user.id,
        type=TransactionType.COURSE_PURCHASE,
        amount=course.price,
        currency=Currency.DT,
        description=f"Achat cours: {course.title}",
        reference_id=f"course_{course_id}",
        status="completed",
    )
    db.add(transaction)

    # Calculer la répartition
    commission_rate = Decimal(str(course.commission_rate or 0))
    platform_fee = course.price * (commission_rate / Decimal("100"))
    teacher_revenue = course.price - platform_fee

    purchase = CoursePurchase(
        student_id=current_user.id,
        course_id=course_id,
        amount_paid=course.price,
        currency=course.currency or "TND",
        platform_fee=platform_fee,
        teacher_revenue=teacher_revenue,
        commission_rate_applied=commission_rate,
        transaction_id=str(transaction.id),
    )
    db.add(purchase)

    # Auto-inscription
    enrollment = CourseEnrollment(
        student_id=current_user.id,
        course_id=course_id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(purchase)

    # Notify course author
    try:
        from app.services.notification_service import notify_purchase
        if course.author_id and course.author_id != current_user.id:
            student_name = current_user.full_name or current_user.email
            notify_purchase(course.author_id, student_name, course.title, course.price, current_user.school_id or 1, db)
    except Exception:
        pass

    return {
        "purchase_id": purchase.id,
        "amount_paid": purchase.amount_paid,
        "currency": purchase.currency,
        "platform_fee": purchase.platform_fee,
        "teacher_revenue": purchase.teacher_revenue,
        "remaining_balance": get_dt_balance(db, current_user.id),
    }


# ---------------------------------------------------------------------------
# 10. Demande de remboursement
# ---------------------------------------------------------------------------

@router.post("/{course_id}/refund-request")
def refund_request(
    course_id: int,
    reason: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """
    Demande de remboursement pour un cours acheté.
    Règles:
    - L'élève ne doit pas avoir dépassé REFUND_MAX_PROGRESS_PERCENT de progression
    - owner_type="eduai_catalog": remboursement automatique (EDUAI absorbe)
    - owner_type="independent_teacher": validation manuelle du super_admin requise
    """
    from app.models import CoursePurchase, LessonProgress, CourseEnrollment
    from app.core.config import get_settings
    settings = get_settings()

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    purchase = db.query(CoursePurchase).filter(
        CoursePurchase.student_id == current_user.id,
        CoursePurchase.course_id == course_id,
        CoursePurchase.refunded == False,
    ).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Achat non trouvé ou déjà remboursé")

    # Vérifier la progression
    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        CourseEnrollment.course_id == course_id,
    ).first()
    if enrollment:
        total_lessons = course.total_lessons or 1
        completed = db.query(func.count(LessonProgress.id)).filter(
            LessonProgress.enrollment_id == enrollment.id,
            LessonProgress.status == "completed",
        ).scalar() or 0
        progress_pct = (completed / total_lessons) * 100
        if progress_pct >= settings.refund_max_progress_percent:
            raise HTTPException(
                status_code=400,
                detail=f"Progression trop avancée ({progress_pct:.0f}%) pour un remboursement (max: {settings.refund_max_progress_percent}%)"
            )

    # Traiter selon owner_type
    if course.owner_type == "eduai_catalog":
        # Remboursement automatique — crediter le DT du prix payé
        from app.services.wallet import credit_dt
        credit_dt(
            db,
            current_user.id,
            purchase.amount_paid,
            source="refund",
            reason=f"Remboursement cours #{course_id}: {reason}",
            commit=False,
        )
        purchase.refunded = True
        purchase.refund_reason = reason
        purchase.refunded_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "refunded", "message": "Remboursement automatique traité"}
    else:
        # owner_type="independent_teacher" ou "school": validation manuelle requise
        purchase.refund_reason = reason
        db.commit()
        return {"status": "pending_validation", "message": "Votre demande de remboursement est en attente de validation par un super admin"}


# ---- CMS Versioning ----

@router.post("/{course_id}/create-draft-version")
def create_draft_version(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    Crée une nouvelle version brouillon d'un cours existant.
    La version actuelle reste active (is_active_version=True).
    La nouvelle version est créée avec is_active_version=False et pedagogical_status="draft".
    """
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    check_school_access(current_user, course.school_id)

    # Incrémente le numéro de version
    new_version_number = course.version_number + 1

    # Crée une copie du cours avec les mêmes données
    new_course = Course(
        school_id=course.school_id,
        author_id=course.author_id,
        modified_by=current_user.id,
        title=f"{course.title} (V{new_version_number})",
        short_description=course.short_description,
        description=course.description,
        thumbnail_url=course.thumbnail_url,
        cover_url=course.cover_url,
        slug=None,  # Auto-généré
        language=course.language,
        prerequisites=course.prerequisites,
        learning_objectives=course.learning_objectives,
        visibility="private",
        enrollment_type=course.enrollment_type,
        owner_type=course.owner_type,
        owner_id=course.owner_id,
        price=course.price,
        currency=course.currency,
        commission_rate=course.commission_rate,
        price_tokens=course.price_tokens,
        price_dt=course.price_dt,
        category=course.category,
        level=course.level,
        niveau_scolaire=course.niveau_scolaire,
        tags=course.tags,
        status="draft",
        is_published=False,
        pedagogical_status="draft",
        version_number=new_version_number,
        is_active_version=False,
        category_cible=course.category_cible,
        tag_pack_requis=course.tag_pack_requis,
    )

    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    # Copie les modules et leçons de la version source
    source_modules = db.query(Module).filter(Module.course_id == course.id).order_by(Module.order).all()
    for source_module in source_modules:
        new_module = Module(
            course_id=new_course.id,
            title=source_module.title,
            description=source_module.description,
            order=source_module.order,
        )
        db.add(new_module)
        db.flush()

        source_lessons = db.query(Lesson).filter(Lesson.module_id == source_module.id).order_by(Lesson.order).all()
        for source_lesson in source_lessons:
            new_lesson = Lesson(
                module_id=new_module.id,
                school_id=new_course.school_id,
                teacher_id=source_lesson.teacher_id,
                title=source_lesson.title,
                content=source_lesson.content,
                content_type=source_lesson.content_type,
                duration_minutes=source_lesson.duration_minutes,
                order=source_lesson.order,
                is_free=source_lesson.is_free,
                video_url=source_lesson.video_url,
                document_url=source_lesson.document_url,
            )
            db.add(new_lesson)

    db.commit()

    return {
        "message": f"Version V{new_version_number} créée en brouillon",
        "new_course_id": new_course.id,
        "version_number": new_version_number,
        "source_course_id": course.id,
    }


@router.post("/{course_id}/publish-version")
def publish_version(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    Publie une version de cours.
    - Exige une validation pédagogique préalable (approved_local / approved_for_b2b).
    - Désactive toutes les autres versions du même cours source
    - Active la version publiée (is_active_version=True)
    - Met à jour le statut et la date de publication
    """
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    allowed_statuses = ("approved_local", "approved_for_b2b")
    if getattr(course, "pedagogical_status", None) not in allowed_statuses:
        raise HTTPException(
            status_code=403,
            detail="Le cours doit être validé par la modération avant d'être publié.",
        )

    if not _can_write_course(current_user, course):
        raise HTTPException(status_code=403, detail="Seul l'auteur du cours ou un administrateur peut publier ses versions")

    check_school_access(current_user, course.school_id)

    if course.is_active_version:
        raise HTTPException(status_code=400, detail="Cette version est déjà active")

    # Trouve toutes les versions du même titre (enlève le suffixe V/N)
    base_title = course.title.split(" (V")[0] if " (V" in course.title else course.title
    all_versions = db.query(Course).filter(
        Course.school_id == course.school_id,
        Course.author_id == course.author_id,
        Course.title.ilike(f"{base_title}%"),
    ).all()

    # Désactive toutes les versions actives existantes
    for version in all_versions:
        if version.is_active_version and version.id != course.id:
            version.is_active_version = False
            version.status = "archived"
            logger.info(f"Version V{version.version_number} désactivée (course_id={version.id})")

    # Active la nouvelle version
    course.is_active_version = True
    course.status = "published"
    course.is_published = True
    course.published_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": f"Version V{course.version_number} publiée avec succès",
        "course_id": course.id,
        "version_number": course.version_number,
        "is_active_version": True,
    }


@router.post("/{course_id}/rollback/{target_version_id}")
def rollback_to_version(
    course_id: int,
    target_version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """
    Rollback vers une version précédente.
    - Désactive la version actuelle
    - Réactive la version cible (target_version_id)
    """
    current_course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()

    if not current_course:
        raise HTTPException(status_code=404, detail="Current version not found")

    if not _can_write_course(current_user, current_course):
        raise HTTPException(status_code=403, detail="Seul l'auteur du cours ou un administrateur peut effectuer un rollback")

    check_school_access(current_user, current_course.school_id)

    target_course = db.query(Course).filter(
        Course.id == target_version_id,
        Course.school_id == current_user.school_id,
    ).first()

    if not target_course:
        raise HTTPException(status_code=404, detail="Target version not found")

    if not current_course.is_active_version:
        raise HTTPException(status_code=400, detail="La version actuelle n'est pas active")

    # Désactive la version actuelle
    current_course.is_active_version = False
    current_course.status = "archived"
    current_course.is_published = False

    # Réactive la version cible
    target_course.is_active_version = True
    target_course.status = "published"
    target_course.is_published = True
    target_course.pedagogical_status = "approved_local"
    target_course.published_at = datetime.now(timezone.utc)
    target_course.validated_by = current_user.id
    target_course.validated_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": f"Rollback vers V{target_course.version_number} effectué",
        "previous_version_id": current_course.id,
        "restored_version_id": target_course.id,
        "version_number": target_course.version_number,
    }


@router.get("/{course_id}/versions")
def list_course_versions(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(set_tenant_context),
):
    """
    Liste toutes les versions d'un cours.
    """
    # Trouve la version active ou la première version
    base_course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id,
    ).first()

    if not base_course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Cherche toutes les versions (même titre sans suffixe V/N)
    base_title = base_course.title.split(" (V")[0] if " (V" in base_course.title else base_course.title
    versions = db.query(Course).filter(
        Course.school_id == current_user.school_id,
        Course.author_id == base_course.author_id,
        Course.title.ilike(f"{base_title}%"),
    ).order_by(Course.version_number.desc()).all()

    return {
        "total": len(versions),
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "is_active_version": v.is_active_version,
                "status": v.status,
                "pedagogical_status": v.pedagogical_status,
                "title": v.title,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "published_at": v.published_at.isoformat() if v.published_at else None,
            }
            for v in versions
        ],
    }