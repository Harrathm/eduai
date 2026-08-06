"""
Bulk Seats B2B - Endpoints for school administrators to purchase and manage bulk seat vouchers.
"""
import secrets
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.deps import require_school_admin_strict, require_admin
from app.models import User, Course, BulkSeatVoucher, CourseEnrollment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schools/bulk-seats", tags=["Bulk Seats"])


class BulkSeatPurchaseRequest(BaseModel):
    formation_id: int = Field(..., description="Course ID with category_cible='Teacher_Training'")
    quantity: int = Field(..., ge=1, le=1000, description="Number of vouchers to generate")


class BulkSeatPurchaseResponse(BaseModel):
    message: str
    vouchers_created: int
    formation_id: int
    codes: list[str]


class VoucherRedeemRequest(BaseModel):
    code: str = Field(..., min_length=10, max_length=50)


class VoucherRedeemResponse(BaseModel):
    message: str
    enrollment_id: int
    course_title: str


@router.post("/purchase", response_model=BulkSeatPurchaseResponse)
def purchase_bulk_seats(
    req: BulkSeatPurchaseRequest,
    current_user: User = Depends(require_school_admin_strict),
    db: Session = Depends(get_db),
):
    """
    Purchase bulk seat vouchers for a Teacher Training formation.
    Only school admins can purchase. The formation must have category_cible='Teacher_Training'.
    """
    # Verify the formation exists and is a Teacher Training course
    course = db.query(Course).filter(
        Course.id == req.formation_id,
        Course.school_id == current_user.school_id,
    ).first()

    if not course:
        raise HTTPException(status_code=404, detail="Formation not found")

    if course.category_cible != "Teacher_Training":
        raise HTTPException(
            status_code=400,
            detail=f"La formation doit être de type 'Teacher_Training'. Type actuel: {course.category_cible}"
        )

    # Generate unique vouchers
    vouchers = []
    codes = []
    for _ in range(req.quantity):
        code = f"BULK-{secrets.token_hex(4).upper()}-{secrets.token_hex(3).upper()}"
        voucher = BulkSeatVoucher(
            school_id=current_user.school_id,
            formation_id=req.formation_id,
            code=code,
            status="unused",
        )
        db.add(voucher)
        vouchers.append(voucher)
        codes.append(code)

    db.commit()

    logger.info(
        f"Bulk seats purchased: {req.quantity} vouchers for formation #{req.formation_id} "
        f"by school #{current_user.school_id}"
    )

    return BulkSeatPurchaseResponse(
        message=f"{req.quantity} voucher(s) créé(s) avec succès",
        vouchers_created=req.quantity,
        formation_id=req.formation_id,
        codes=codes,
    )


@router.get("/list")
def list_bulk_seats(
    current_user: User = Depends(require_school_admin_strict),
    db: Session = Depends(get_db),
):
    """List all bulk seat vouchers for the current school."""
    vouchers = db.query(BulkSeatVoucher).filter(
        BulkSeatVoucher.school_id == current_user.school_id,
    ).order_by(BulkSeatVoucher.created_at.desc()).all()

    return {
        "total": len(vouchers),
        "unused": sum(1 for v in vouchers if v.status == "unused"),
        "consumed": sum(1 for v in vouchers if v.status == "consumed"),
        "vouchers": [
            {
                "id": v.id,
                "code": v.code,
                "formation_id": v.formation_id,
                "status": v.status,
                "consumed_by": v.consumed_by,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in vouchers
        ],
    }


@router.post("/redeem", response_model=VoucherRedeemResponse)
def redeem_voucher(
    req: VoucherRedeemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Redeem a bulk seat voucher code.
    - Consumes the voucher (status='consumed')
    - Enrolls the user in the formation automatically
    - Links the user to the school if not already linked
    """
    # Find the voucher
    voucher = db.query(BulkSeatVoucher).filter(
        BulkSeatVoucher.code == req.code,
    ).first()

    if not voucher:
        raise HTTPException(status_code=404, detail="Code de voucher invalide")

    if voucher.status == "consumed":
        raise HTTPException(status_code=400, detail="Ce voucher a déjà été utilisé")

    # Get the formation
    course = db.query(Course).filter(Course.id == voucher.formation_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Formation introuvable")

    # Consume the voucher
    voucher.status = "consumed"
    voucher.consumed_by = current_user.id

    # Link user to school if not already linked
    if not current_user.school_id:
        current_user.school_id = voucher.school_id

    # Create enrollment
    existing_enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        CourseEnrollment.course_id == voucher.formation_id,
    ).first()

    if existing_enrollment:
        raise HTTPException(status_code=400, detail="Vous êtes déjà inscrit à cette formation")

    enrollment = CourseEnrollment(
        course_id=voucher.formation_id,
        student_id=current_user.id,
        enrolled_at=datetime.now(timezone.utc),
    )
    db.add(enrollment)
    db.commit()

    logger.info(
        f"Voucher redeemed: code={req.code}, user_id={current_user.id}, "
        f"formation_id={voucher.formation_id}"
    )

    return VoucherRedeemResponse(
        message="Voucher utilisé avec succès. Vous êtes inscrit à la formation.",
        enrollment_id=enrollment.id,
        course_title=course.title,
    )
