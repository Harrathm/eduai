"""
Teacher Revenue Share - Endpoints for teachers to view their revenue report.
"""
import logging
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.auth import get_current_user
from app.deps import set_tenant_context
from app.models import User, TeacherRevenueLedger, Lesson, Course

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teacher", tags=["Teacher Revenue"])


class RevenueSummary(BaseModel):
    total_revenue: float
    total_consumptions: int
    lessons_count: int
    period_start: str
    period_end: str


class LessonRevenue(BaseModel):
    lesson_id: int
    lesson_title: str
    course_title: str
    consumption_count: int
    revenue_amount: float


class RevenueReport(BaseModel):
    summary: RevenueSummary
    lessons: list[LessonRevenue]


def get_teacher_revenue(teacher_id: int, db: Session, month: Optional[date] = None) -> dict:
    """
    Retrieve revenue data for a teacher from the teacher_revenue_ledger.
    
    Args:
        teacher_id: The teacher's user ID
        db: Database session
        month: Optional specific month to query (defaults to current month)
    
    Returns:
        dict with summary and lessons breakdown
    """
    if month is None:
        today = date.today()
        month = date(today.year, today.month, 1)
    
    # Get all revenue entries for this teacher in the specified month
    entries = db.query(TeacherRevenueLedger).filter(
        TeacherRevenueLedger.teacher_id == teacher_id,
        TeacherRevenueLedger.period_month == month,
    ).all()
    
    # Calculate totals
    total_revenue = sum(float(entry.revenue_amount) for entry in entries)
    total_consumptions = sum(entry.consumption_count for entry in entries)
    
    # Group by lesson
    lessons_map = {}
    for entry in entries:
        lesson_id = entry.lesson_id
        if lesson_id not in lessons_map:
            # Get lesson and course info
            lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
            course = None
            if lesson and lesson.module_id:
                from app.models import Module
                module = db.query(Module).filter(Module.id == lesson.module_id).first()
                if module:
                    course = db.query(Course).filter(Course.id == module.course_id).first()
            
            lessons_map[lesson_id] = {
                "lesson_id": lesson_id,
                "lesson_title": lesson.title if lesson else "Unknown Lesson",
                "course_title": course.title if course else "Unknown Course",
                "consumption_count": 0,
                "revenue_amount": 0.0,
            }
        
        lessons_map[lesson_id]["consumption_count"] += entry.consumption_count
        lessons_map[lesson_id]["revenue_amount"] += float(entry.revenue_amount)
    
    # Sort by revenue descending
    lessons_list = sorted(lessons_map.values(), key=lambda x: x["revenue_amount"], reverse=True)
    
    return {
        "summary": {
            "total_revenue": total_revenue,
            "total_consumptions": total_consumptions,
            "lessons_count": len(lessons_list),
            "period_start": month.isoformat(),
            "period_end": month.isoformat(),
        },
        "lessons": lessons_list,
    }


@router.get("/revenue-report", response_model=RevenueReport)
def get_revenue_report(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format (defaults to current month)"),
    current_user: User = Depends(set_tenant_context),
    db: Session = Depends(get_db),
):
    """
    Get revenue report for the current teacher.
    Only accessible to teachers with is_partner=True.
    """
    # Check if user is a teacher
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=403,
            detail="Cet endpoint est réservé aux enseignants"
        )
    
    # Check if teacher is a partner
    if not current_user.is_partner:
        raise HTTPException(
            status_code=403,
            detail="Vous devez être partenaire pour accéder au rapport de revenus"
        )
    
    # Parse month parameter
    target_month = None
    if month:
        try:
            year, mon = map(int, month.split("-"))
            target_month = date(year, mon, 1)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail="Format de mois invalide. Utilisez YYYY-MM (ex: 2026-08)"
            )
    
    report = get_teacher_revenue(current_user.id, db, target_month)
    return RevenueReport(**report)


@router.get("/revenue-history")
def get_revenue_history(
    months: int = Query(6, ge=1, le=12, description="Number of months to retrieve"),
    current_user: User = Depends(set_tenant_context),
    db: Session = Depends(get_db),
):
    """
    Get revenue history for the last N months.
    Only accessible to teachers with is_partner=True.
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=403,
            detail="Cet endpoint est réservé aux enseignants"
        )
    
    if not current_user.is_partner:
        raise HTTPException(
            status_code=403,
            detail="Vous devez être partenaire pour accéder à l'historique des revenus"
        )
    
    # Get revenue for each month
    history = []
    today = date.today()
    
    for i in range(months):
        # Calculate month
        year = today.year
        month_num = today.month - i
        while month_num <= 0:
            month_num += 12
            year -= 1
        
        target_month = date(year, month_num, 1)
        report = get_teacher_revenue(current_user.id, db, target_month)
        
        history.append({
            "month": target_month.isoformat(),
            "total_revenue": report["summary"]["total_revenue"],
            "total_consumptions": report["summary"]["total_consumptions"],
            "lessons_count": report["summary"]["lessons_count"],
        })
    
    # Calculate totals
    total_revenue_all = sum(h["total_revenue"] for h in history)
    total_consumptions_all = sum(h["total_consumptions"] for h in history)
    
    return {
        "teacher_id": current_user.id,
        "is_partner": current_user.is_partner,
        "total_revenue": total_revenue_all,
        "total_consumptions": total_consumptions_all,
        "months_requested": months,
        "history": history,
    }
