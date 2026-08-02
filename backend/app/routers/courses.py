"""Courses API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone

from app.db import get_db
from app.auth import get_current_user
from app.deps import set_tenant_context, check_school_access, require_teacher_or_admin
from app.models import User, Course, Module, Lesson, CourseEnrollment
from app.models import UserRole, CourseStatus, Transaction, TransactionType, Currency
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
    """Get course by ID"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == current_user.school_id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return course


@router.post("", response_model=CourseRead)
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """Create a new course (teachers and admins only)"""
    course = Course(
        **course_in.model_dump(),
        school_id=current_user.school_id,
        author_id=current_user.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return course


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
    
    check_school_access(current_user, course.school_id)
    
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
        raise HTTPException(status_code=403, detail="Not authorized")
    
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
    transaction = Transaction(
        school_id=current_user.school_id or course.school_id or 1,
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