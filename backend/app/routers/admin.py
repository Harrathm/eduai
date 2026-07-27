from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FastAPIFile
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Any
import logging
import json
import csv
import io
import secrets

from app.db import get_db
from app.auth import get_current_user
from app.deps import require_admin, require_platform_admin, require_school_admin_strict, require_super_admin, check_school_access, get_user_role, require_non_demo_access
from app.models import User, School, ClassRoom, Course, Assignment, Submission, Module, Lesson, Quiz, TeacherRegistration, Transaction, TokenPackage, CoursePurchase, Message, PlatformSettings, Plan, TransactionType, SchoolType, UserRole, WalletPool, LessonProgress
from app.core.security import get_password_hash
from app.core.validation import validate_password_strength
from app.schemas import (
    UserRead, UserUpdate, SchoolCreate, SchoolRead, ClassCreate, ClassRead,
    EnrollmentCreate, EnrollmentRead, CourseRead, AssignmentCreate, AssignmentRead,
    AnalyticsOverview, UserAnalytics, UserBalanceUpdate, UserApproval,
    CourseCreate, CourseUpdate, CourseStatusUpdate, CourseWithDetails,
    ModuleCreate, ModuleUpdate, LessonCreate, LessonUpdate, LessonMediaCreate,
    QuizCreate, TeacherRegistrationCreate, TeacherRegistrationUpdate, TeacherRegistrationRead,
    TransactionCreate, TransactionRead, TokenPackageCreate, TokenPackageRead,
    AdminDashboardStats, UserDetail,
    MessageCreate, MessageRead, SettingsUpdate, SettingsRead
)

logger = logging.getLogger(__name__)


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list


router = APIRouter()


def audit_log(db: Session, admin_id: int, admin_email: str, action: str, target_type: str = None, target_id: int = None, details: str = None, ip: str = None):
    from app.models import AuditLog
    log = AuditLog(
        admin_id=admin_id,
        admin_email=admin_email,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip,
    )
    db.add(log)
    try:
        db.commit()
    except Exception:
        db.rollback()


def _is_super(admin: User) -> bool:
    return get_user_role(admin) == "super_admin"


def _super_or_school_filter(query, admin: User, school_field):
    if _is_super(admin):
        return query
    return query.filter(school_field == admin.school_id)


# ---- Schools ----

@router.post("/schools", response_model=SchoolRead)
def create_school(school_in: SchoolCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    slug = school_in.slug or school_in.name.lower().replace(" ", "-").replace("'", "")
    existing = db.query(School).filter(School.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="School slug already exists")
    data = school_in.model_dump(exclude_unset=True)
    data["slug"] = slug
    data["invite_code"] = secrets.token_urlsafe(8)
    school = School(**data)
    db.add(school)
    db.commit()
    db.refresh(school)

    audit_log(db, admin.id, admin.email or "unknown", "school.create",
        target_type="school", target_id=school.id,
        details=f"created school '{school.name}' with tier {school.subscription_tier}")

    return school


@router.get("/schools")
def list_schools(
    search: str | None = None,
    tier: str | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    query = db.query(School)
    if search:
        st = f"%{search}%"
        query = query.filter((School.name.ilike(st)) | (School.domain.ilike(st)))
    if tier:
        query = query.filter(School.subscription_tier == tier)
    if is_active is not None:
        query = query.filter(School.is_active == is_active)

    total = query.count()
    schools = query.order_by(School.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "page": page, "per_page": per_page, "items": schools}


@router.get("/schools/{school_id}", response_model=SchoolRead)
def get_school(school_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    check_school_access(admin, school.id)
    return school


@router.put("/schools/{school_id}", response_model=SchoolRead)
def update_school(school_id: int, school_in: SchoolCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    check_school_access(admin, school_id)
    for k, v in school_in.model_dump(exclude_unset=True).items():
        setattr(school, k, v)
    db.commit()
    db.refresh(school)
    return school


@router.post("/schools/{school_id}/regenerate-invite-code")
def regenerate_invite_code(school_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    import secrets
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    check_school_access(admin, school_id)
    school.invite_code = secrets.token_urlsafe(8)
    db.commit()
    return {"invite_code": school.invite_code}


# ---- Users ----

@router.get("/users", response_model=PaginatedResponse)
def list_users(
    role: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|full_name|email|role)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
    _demo_guard=Depends(require_non_demo_access),
):
    if _is_super(admin):
        query = db.query(User)
    else:
        query = db.query(User).filter(User.school_id == admin.school_id)

    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_term)) |
            (User.email.ilike(search_term))
        )

    total = query.count()
    sort_col = getattr(User, sort_by, User.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    users = query.offset((page - 1) * per_page).limit(per_page).all()

    school_ids = list(set(u.school_id for u in users))
    schools = {s.id: s.name for s in db.query(School).filter(School.id.in_(school_ids)).all()}

    result = []
    for user in users:
        result.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "school_id": user.school_id,
            "school_name": schools.get(user.school_id, "Unknown"),
            "role": user.role,
            "token_balance": user.token_balance or 0,
            "dt_balance": user.dt_balance or 0.0,
            "is_approved": user.is_approved,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "total_dt_earned": 0.0,
            "total_tokens_spent": 0,
            "total_dt_spent": 0.0,
        })

    return {"total": total, "page": page, "per_page": per_page, "items": result}


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.school_id is not None:
        check_school_access(admin, user.school_id)
    return user


# Instead of /users/{user_id}, use /user-update endpoint
@router.post("/user-update")
def user_update_post(
    user_id: int,
    is_active: bool | None = None,
    token_balance: int | None = None,
    dt_balance: float | None = None,
    role: str | None = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    if _is_super(admin):
        pass  # super sees all
    else:
        if user.school_id != admin.school_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    if is_active is not None:
        user.is_active = is_active
    if token_balance is not None:
        user.token_balance = token_balance
    if dt_balance is not None:
        user.dt_balance = dt_balance
    if role:
        user.role = role
    
    db.commit()
    db.refresh(user)
    
    return {"success": True, "user": {"id": user.id, "email": user.email, "is_active": user.is_active, "token_balance": user.token_balance, "dt_balance": user.dt_balance, "role": str(user.role)}}


@router.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: int, body: dict, db: Session = Depends(get_db), admin=Depends(require_admin)):
    if _is_super(admin):
        user = db.query(User).filter(User.id == user_id).first()
    else:
        user = db.query(User).filter(User.id == user_id, User.school_id == admin.school_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_password = body.get("new_password", "")
    if not new_password:
        raise HTTPException(status_code=422, detail="new_password is required")
    ok, err = validate_password_strength(new_password)
    if not ok:
        raise HTTPException(status_code=422, detail=err)
    user.hashed_password = get_password_hash(body["new_password"])
    db.commit()
    return {"ok": True}


@router.post("/users")
def create_user(
    email: str,
    password: str,
    full_name: str | None = None,
    role: str = "student",
    school_id: int | None = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    if _is_super(admin):
        target_school_id = school_id or admin.school_id
    else:
        target_school_id = admin.school_id

    if not target_school_id:
        raise HTTPException(status_code=400, detail="Aucune école spécifiée. Le super admin doit fournir un school_id.")

    # RBAC: restrict which roles can be assigned
    if _is_super(admin):
        allowed_roles = {"student", "teacher", "admin_school", "pedagogical_admin", "pedagogical_lead", "super_admin"}
    else:
        allowed_roles = {"student", "teacher"}
    if role not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Cannot assign role '{role}'. Allowed: {sorted(allowed_roles)}")

    school = db.query(School).filter(School.id == target_school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail=f"École #{target_school_id} introuvable.")
    max_users = school.max_users if school.max_users else 10
    current_count = db.query(User).filter(User.school_id == target_school_id).count()
    
    if current_count >= max_users:
        raise HTTPException(status_code=400, detail=f"User limit reached. Maximum {max_users} users allowed for {school.subscription_tier} tier.")
    
    existing = db.query(User).filter(User.email == email, User.school_id == target_school_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered in this school")
    ok, err = validate_password_strength(password)
    if not ok:
        raise HTTPException(status_code=422, detail=err)
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=role,
        school_id=target_school_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user)


# ---- Classes ----

@router.get("/classes")
def list_classes(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    if _is_super(admin):
        query = db.query(ClassRoom)
    else:
        query = db.query(ClassRoom).filter(ClassRoom.school_id == admin.school_id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.post("/classes", response_model=ClassRead)
def create_class(class_in: ClassCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    target_school = admin.school_id
    existing = db.query(ClassRoom).filter(
        ClassRoom.school_id == target_school, ClassRoom.code == class_in.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Class code already exists in this school")
    cls = ClassRoom(**class_in.model_dump(), school_id=target_school)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


@router.post("/enrollments", response_model=EnrollmentRead)
def enroll_student(enroll_in: EnrollmentCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    from app.models import Enrollment
    existing = db.query(Enrollment).filter(
        Enrollment.school_id == admin.school_id,
        Enrollment.user_id == enroll_in.user_id,
        Enrollment.class_id == enroll_in.class_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already enrolled in this class")
    enrollment = Enrollment(**enroll_in.model_dump(), school_id=admin.school_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.get("/enrollments")
def list_enrollments(
    class_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    from app.models import Enrollment
    query = db.query(Enrollment).filter(Enrollment.school_id == admin.school_id)
    if class_id:
        query = query.filter(Enrollment.class_id == class_id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/analytics/overview", response_model=AnalyticsOverview)
def analytics_overview(db: Session = Depends(get_db), admin=Depends(require_admin), _demo_guard=Depends(require_non_demo_access)):
    from sqlalchemy import func

    if _is_super(admin):
        total_users = db.query(User).count()
        total_students = db.query(User).filter(User.role == "student").count()
        total_teachers = db.query(User).filter(User.role == "teacher").count()
        total_courses = db.query(Course).count()
        total_assignments = db.query(Assignment).count()
        submissions = db.query(Submission).all()
    else:
        total_users = db.query(User).filter(User.school_id == admin.school_id).count()
        total_students = db.query(User).filter(User.school_id == admin.school_id, User.role == "student").count()
        total_teachers = db.query(User).filter(User.school_id == admin.school_id, User.role == "teacher").count()
        total_courses = db.query(Course).filter(Course.school_id == admin.school_id).count()
        total_assignments = db.query(Assignment).join(Assignment.classroom).filter(ClassRoom.school_id == admin.school_id).count()
        submissions = db.query(Submission).join(Assignment).join(Assignment.classroom).filter(ClassRoom.school_id == admin.school_id).all()

    total_submissions = len(submissions)
    pending_submissions = sum(1 for s in submissions if s.grade is None)

    ai_requests = 0
    ai_cost = 0.0

    return AnalyticsOverview(
        total_users=total_users,
        total_students=total_students,
        total_teachers=total_teachers,
        total_courses=total_courses,
        total_assignments=total_assignments,
        total_submissions=total_submissions,
        pending_submissions=pending_submissions,
        ai_requests=ai_requests,
        ai_cost_usd=float(ai_cost),
    )


@router.get("/analytics/users")
def user_analytics(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    from app.models import Submission

    if _is_super(admin):
        users_query = db.query(User)
    else:
        users_query = db.query(User).filter(User.school_id == admin.school_id)
    total = users_query.count()
    users = users_query.offset(skip).limit(limit).all()
    result = []
    for user in users:
        subs = db.query(Submission).filter(Submission.student_id == user.id).all()
        grades = [s.grade for s in subs if s.grade is not None]
        avg_grade = sum(grades) / len(grades) if grades else None

        result.append(UserAnalytics(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            ai_requests=0,
            ai_cost_usd=0.0,
            submissions_count=len(subs),
            avg_grade=avg_grade,
        ))
    return {"total": total, "skip": skip, "limit": limit, "items": result}


# ---- User Management with Balance ----

@router.get("/users-all")
def list_users_detail(
    role: str | None = None,
    is_approved: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
    _demo_guard=Depends(require_non_demo_access),
):
    if _is_super(admin):
        query = db.query(User)
    else:
        query = db.query(User).filter(User.school_id == admin.school_id)
    if role:
        query = query.filter(User.role == role)
    if is_approved is not None:
        query = query.filter(User.is_approved == is_approved)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


class UserEditRequest(BaseModel):
    full_name: str | None = None
    email: str | None = None
    role: str | None = None
    school_id: int | None = None
    is_active: bool | None = None
    is_approved: bool | None = None


@router.put("/users/{user_id}")
def update_user(user_id: int, body: UserEditRequest, db: Session = Depends(get_db), admin=Depends(require_admin)):
    """Full user edit (super_admin only for cross-school changes)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_super = _is_super(admin)
    if not is_super and user.school_id != admin.school_id:
        raise HTTPException(status_code=403, detail="Access denied")

    changes = {}
    if body.full_name is not None:
        user.full_name = body.full_name
        changes["full_name"] = body.full_name
    if body.email is not None:
        existing = db.query(User).filter(User.email == body.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = body.email
        changes["email"] = body.email
    if body.role is not None:
        if not is_super and body.role == "super_admin":
            raise HTTPException(status_code=403, detail="Only super_admin can promote to super_admin")
        valid = ["student", "teacher", "admin_school", "pedagogical_admin", "pedagogical_lead", "super_admin"]
        if body.role not in valid:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid}")
        user.role = body.role
        changes["role"] = body.role
    if body.school_id is not None:
        if not is_super:
            raise HTTPException(status_code=403, detail="Only super_admin can change school")
        school = db.query(School).filter(School.id == body.school_id).first()
        if not school:
            raise HTTPException(status_code=400, detail="School not found")
        user.school_id = body.school_id
        changes["school_id"] = body.school_id
    if body.is_active is not None:
        user.is_active = body.is_active
        changes["is_active"] = body.is_active
    if body.is_approved is not None:
        user.is_approved = body.is_approved
        changes["is_approved"] = body.is_approved

    db.commit()
    db.refresh(user)

    audit_log(db, admin.id, admin.email or "admin",
        "user.update", target_type="user", target_id=user.id,
        details=f"updated fields: {json.dumps(changes)}")

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "school_id": user.school_id,
        "is_active": user.is_active,
        "is_approved": user.is_approved,
    }


@router.put("/users/{user_id}/balance", response_model=UserDetail)
def update_user_balance(user_id: int, balance: UserBalanceUpdate, db: Session = Depends(get_db), admin=Depends(require_platform_admin)):
    if _is_super(admin):
        user = db.query(User).filter(User.id == user_id).first()
    else:
        user = db.query(User).filter(User.id == user_id, User.school_id == admin.school_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if balance.tokens is not None:
        user.token_balance = balance.tokens
    if balance.dt_balance is not None:
        user.dt_balance = balance.dt_balance
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/toggle-active", response_model=dict)
def toggle_user_active(user_id: int, db: Session = Depends(get_db), admin=Depends(require_platform_admin)):
    """Toggle user active status (suspend/reactivate)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.school_id is not None:
        check_school_access(admin, user.school_id)
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    audit_log(db, admin.id, admin.email or "unknown", "user.update",
        target_type="user", target_id=user.id,
        details=f"toggled active={user.is_active}")

    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "message": f"User {'activated' if user.is_active else 'suspended'} successfully"
    }


@router.put("/users/{user_id}/change-role", response_model=dict)
def change_user_role(user_id: int, new_role: str, db: Session = Depends(get_db), admin=Depends(require_platform_admin)):
    """Change user role - super_admin can change any role, admin can change within their school"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    valid_roles = ["student", "teacher", "admin_school", "pedagogical_admin", "pedagogical_lead", "super_admin"]
    if new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    if _is_super(admin):
        pass  # super can change any role
    else:
        if user.school_id != admin.school_id:
            raise HTTPException(status_code=403, detail="You can only change roles for users in your school")
        if new_role == "super_admin":
            raise HTTPException(status_code=403, detail="Only super_admin can promote to super_admin")
        # Non-super admins cannot assign privileged roles
        non_super_allowed = {"student", "teacher"}
        if new_role not in non_super_allowed:
            raise HTTPException(status_code=403, detail=f"Cannot assign role '{new_role}'. Allowed: {sorted(non_super_allowed)}")
    
    old_role = str(user.role) if user.role else "unknown"
    user.role = new_role
    db.commit()
    db.refresh(user)

    audit_log(db, admin.id, admin.email or "unknown", "user.role_change",
        target_type="user", target_id=user.id,
        details={"old_role": old_role, "new_role": new_role})

    return {
        "id": user.id,
        "email": user.email,
        "old_role": old_role,
        "new_role": new_role,
        "message": f"Role changed to {new_role} successfully"
    }


@router.put("/users/{user_id}/approve", response_model=UserDetail)
def approve_user(user_id: int, approval: UserApproval, db: Session = Depends(get_db), admin=Depends(require_platform_admin)):
    if _is_super(admin):
        user = db.query(User).filter(User.id == user_id).first()
    else:
        user = db.query(User).filter(User.id == user_id, User.school_id == admin.school_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_approved = approval.approved
    user.approved_by = admin.id
    user.approved_at = datetime.now(timezone.utc)
    if not approval.approved and approval.rejection_reason:
        user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.post("/transactions", response_model=TransactionRead)
def create_transaction(trans_in: TransactionCreate, db: Session = Depends(get_db), admin=Depends(require_platform_admin)):
    if _is_super(admin):
        user = db.query(User).filter(User.id == trans_in.user_id).first()
    else:
        user = db.query(User).filter(User.id == trans_in.user_id, User.school_id == admin.school_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    transaction = Transaction(
        user_id=trans_in.user_id,
        type=trans_in.type,
        amount=trans_in.amount,
        currency=trans_in.currency,
        description=trans_in.description,
        school_id=admin.school_id,
    )
    db.add(transaction)
    
    if trans_in.type == "token_purchase":
        user.token_balance += int(trans_in.amount)
    elif trans_in.type == "token_spend":
        user.token_balance -= int(trans_in.amount)
    
    db.commit()
    db.refresh(transaction)
    return transaction


# ---- Token Packages ----

@router.get("/token-packages")
def list_token_packages(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    query = db.query(TokenPackage).filter(TokenPackage.is_active == True)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.post("/token-packages", response_model=TokenPackageRead)
def create_token_package(pkg_in: TokenPackageCreate, db: Session = Depends(get_db), admin=Depends(require_platform_admin)):
    pkg = TokenPackage(**pkg_in.model_dump())
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


@router.put("/token-packages/{pkg_id}", response_model=TokenPackageRead)
def update_token_package(pkg_id: int, pkg_in: TokenPackageCreate, db: Session = Depends(get_db), admin=Depends(require_platform_admin)):
    pkg = db.query(TokenPackage).filter(TokenPackage.id == pkg_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    for k, v in pkg_in.model_dump(exclude_unset=True).items():
        setattr(pkg, k, v)
    db.commit()
    db.refresh(pkg)
    return pkg


@router.get("/dashboard/stats", response_model=AdminDashboardStats)
@router.get("/dashboard", response_model=AdminDashboardStats)
def dashboard_stats(db: Session = Depends(get_db), admin=Depends(require_admin), _demo_guard=Depends(require_non_demo_access)):
    from app.models import TeacherRegistration, Transaction
    from sqlalchemy import func
    
    is_super = _is_super(admin)
    
    if is_super:
        total_users = db.query(User).count()
        total_teachers = db.query(User).filter(User.role.in_(["teacher"])).count()
        total_students = db.query(User).filter(User.role.in_(["student"])).count()
        total_courses = db.query(Course).count()
        pending_courses = db.query(Course).filter(Course.is_published == False).count()
        published_courses = db.query(Course).filter(Course.is_published == True).count()
        pending_teacher_registrations = db.query(TeacherRegistration).filter(TeacherRegistration.status == "pending").count()
        total_transactions_amt = db.query(func.sum(Transaction.amount)).filter(Transaction.status == "completed").scalar() or 0.0
        tokens_purchased = db.query(func.sum(Transaction.amount)).filter(Transaction.type == TransactionType.TOKEN_RECHARGE).scalar() or 0
    else:
        total_users = db.query(User).filter(User.school_id == admin.school_id).count()
        total_teachers = db.query(User).filter(User.school_id == admin.school_id, User.role.in_(["teacher"])).count()
        total_students = db.query(User).filter(User.school_id == admin.school_id, User.role.in_(["student"])).count()
        total_courses = db.query(Course).filter(Course.school_id == admin.school_id).count()
        pending_courses = db.query(Course).filter(Course.school_id == admin.school_id, Course.is_published == False).count()
        published_courses = db.query(Course).filter(Course.school_id == admin.school_id, Course.is_published == True).count()
        pending_teacher_registrations = db.query(TeacherRegistration).filter(
            TeacherRegistration.school_id == admin.school_id, TeacherRegistration.status == "pending"
        ).count()
        total_transactions_amt = db.query(func.sum(Transaction.amount)).filter(
            Transaction.school_id == admin.school_id, Transaction.status == "completed"
        ).scalar() or 0.0
        tokens_purchased = db.query(func.sum(Transaction.amount)).filter(
            Transaction.school_id == admin.school_id,
            Transaction.type == TransactionType.TOKEN_RECHARGE
        ).scalar() or 0
    
    return AdminDashboardStats(
        total_users=total_users,
        total_teachers=total_teachers,
        total_students=total_students,
        total_courses=total_courses,
        pending_courses=pending_courses,
        published_courses=published_courses,
        pending_teacher_registrations=pending_teacher_registrations,
        total_transactions=float(total_transactions_amt),
        total_tokens_sold=int(tokens_purchased or 0),
        total_dt_revenue=float(total_transactions_amt),
    )


# ---- Messages ----

@router.get("/messages")
def list_messages(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    user_role = _is_super(admin)
    if user_role:
        query = db.query(Message)
    else:
        query = db.query(Message).filter(Message.school_id == admin.school_id)
    total = query.count()
    messages = query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for msg in messages:
        result.append(MessageRead(
            id=msg.id,
            type=msg.type,
            subject=msg.subject,
            body=msg.body,
            sender_id=msg.sender_id,
            sender_name=msg.sender.full_name if msg.sender else "Admin",
            recipient_id=msg.recipient_id,
            recipient_name=msg.recipient.full_name if msg.recipient else None,
            recipient_role=msg.recipient_role,
            target_audience=msg.target_audience,
            is_read=msg.is_read,
            created_at=msg.created_at,
        ))
    return {"total": total, "skip": skip, "limit": limit, "items": result}


@router.post("/messages", response_model=MessageRead)
def create_message(
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    if message_in.type == "direct" and not message_in.recipient_id:
        raise HTTPException(status_code=400, detail="Recipient required for direct message")
    
    message = Message(
        type=message_in.type,
        subject=message_in.subject,
        body=message_in.body,
        sender_id=admin.id,
        recipient_id=message_in.recipient_id,
        recipient_role=message_in.recipient_role,
        school_id=admin.school_id,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return MessageRead(
        id=message.id,
        type=message.type,
        subject=message.subject,
        body=message.body,
        sender_id=message.sender_id,
        sender_name=admin.full_name or "Admin",
        recipient_id=message.recipient_id,
        recipient_name=message.recipient.full_name if message.recipient else None,
        recipient_role=message.recipient_role,
        target_audience=message.target_audience,
        is_read=message.is_read,
        created_at=message.created_at,
    )


@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.school_id == admin.school_id
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db.delete(message)
    db.commit()
    return {"status": "deleted"}


# ---- Broadcast ----

class BroadcastRequest(BaseModel):
    target: str = "all"  # all, teachers_only, students_only, admins_only
    subject: str
    body: str


@router.post("/broadcast")
def broadcast_message(
    body: BroadcastRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """Send a broadcast to a user segment. Uses the modular NotificationService."""
    from app.services import NotificationService

    valid_targets = ["all", "teachers_only", "students_only", "admins_only"]
    if body.target not in valid_targets:
        raise HTTPException(status_code=400, detail=f"Invalid target. Must be one of: {valid_targets}")

    svc = NotificationService(db, sender_id=admin.id, school_id=admin.school_id)
    audience_count = svc.get_audience_count(body.target)
    messages = svc.broadcast(body.subject, body.body, body.target)

    audit_log(db, admin.id, admin.email or "admin",
        "broadcast.send", target_type="broadcast",
        details=f"target={body.target} subject='{body.subject}' audience_count={audience_count}")

    return {
        "ok": True,
        "target": body.target,
        "audience_count": audience_count,
        "messages_created": len(messages),
        "subject": body.subject,
    }


# ---- Platform Settings ----

@router.get("/settings", response_model=list[SettingsRead])
def list_settings(
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    platform_keys = {"ai_providers_config", "maintenance_mode", "allow_teacher_registration", "allow_new_signups"}

    # Non-super_admin only sees their school's settings
    if not _is_super(admin):
        settings = db.query(PlatformSettings).filter(
            PlatformSettings.school_id == admin.school_id,
            PlatformSettings.key.notin_(platform_keys),
        ).all()
        return settings

    # Super admin sees platform + school settings
    settings = db.query(PlatformSettings).filter(
        (PlatformSettings.school_id == admin.school_id) |
        (PlatformSettings.school_id == None)
    ).all()
    return settings


@router.put("/settings", response_model=SettingsRead)
def update_setting(
    setting_in: SettingsUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Updating setting: key={setting_in.key}, school_id={admin.school_id}")
    
    # Platform-wide settings (no school_id needed)
    platform_keys = ["ai_providers_config", "maintenance_mode", "allow_teacher_registration", "allow_new_signups"]
    is_platform = setting_in.key in platform_keys
    
    if is_platform:
        # Only super_admin can modify platform-wide settings
        if not _is_super(admin):
            raise HTTPException(status_code=403, detail="Only super admin can modify platform settings")
    
    if is_platform:
        # Platform-wide: use school_id = None or first school (id=1)
        setting = db.query(PlatformSettings).filter(
            PlatformSettings.key == setting_in.key,
            PlatformSettings.school_id == None
        ).first()
    else:
        # School-specific
        setting = db.query(PlatformSettings).filter(
            PlatformSettings.key == setting_in.key,
            PlatformSettings.school_id == admin.school_id
        ).first()
    
    if setting:
        setting.value = setting_in.value
        if setting_in.description:
            setting.description = setting_in.description
    else:
        school_id = None if is_platform else admin.school_id
        setting = PlatformSettings(
            key=setting_in.key,
            value=setting_in.value,
            description=setting_in.description,
            school_id=school_id,
        )
        db.add(setting)
    
    db.commit()
    db.refresh(setting)

    # Invalidate cache so changes take effect immediately
    try:
        from app.services.settings_service import settings_cache
        settings_cache.invalidate(admin.school_id)
        if is_platform:
            settings_cache.invalidate(0)  # platform-level
    except Exception:
        pass

    # Audit log
    audit_log(db, admin.id, admin.email, "settings.update",
              target_type="setting", target_id=setting.id,
              details=f"Updated key='{setting_in.key}'")

    # Runtime env var rotation for AI providers
    if setting_in.key == "ai_providers_config" and setting_in.value:
        import os
        try:
            providers = json.loads(setting_in.value)
            env_map = {
                "openai": "OPENAI_API_KEY",
                "groq": "GROQ_API_KEY",
                "openrouter": "OPENROUTER_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "azure": "AZURE_OPENAI_KEY",
                "google": "GOOGLE_API_KEY",
            }
            for pid, pcfg in providers.items():
                if pcfg.get("enabled") and pcfg.get("key") and pid in env_map:
                    os.environ[env_map[pid]] = pcfg["key"]
                    logger.info(f"Runtime {pid} API key updated via PUT")
        except Exception:
            pass
    if setting_in.key == "openai_api_key" and setting_in.value:
        import os
        os.environ["OPENAI_API_KEY"] = setting_in.value

    return setting


@router.post("/settings/apply")
def apply_settings(
    settings_list: list[SettingsUpdate],
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """Apply multiple settings at once and immediately invalidate cache."""
    import logging
    logger = logging.getLogger(__name__)
    results = []
    platform_keys = ["ai_providers_config", "maintenance_mode", "allow_teacher_registration", "allow_new_signups",
                     "token_limits", "maintenance_message", "openai_api_key", "stripe_secret_key"]

    # Check super_admin for platform settings
    has_platform = any(item.key in platform_keys for item in settings_list)
    if has_platform and not _is_super(admin):
        raise HTTPException(status_code=403, detail="Only super admin can modify platform settings")

    for item in settings_list:
        is_platform = item.key in platform_keys
        school_id = None if is_platform else admin.school_id
        setting = db.query(PlatformSettings).filter(
            PlatformSettings.key == item.key,
            PlatformSettings.school_id == school_id,
        ).first()
        if setting:
            setting.value = item.value
        else:
            setting = PlatformSettings(key=item.key, value=item.value, school_id=school_id)
            db.add(setting)
        results.append({"key": item.key, "value": item.value})
    db.commit()

    # Invalidate all caches
    try:
        from app.services.settings_service import settings_cache
        settings_cache.invalidate(admin.school_id)
        settings_cache.invalidate(0)
    except Exception:
        pass

    # Handle runtime API key rotation
    for item in settings_list:
        if item.key == "openai_api_key" and item.value:
            import os
            os.environ["OPENAI_API_KEY"] = item.value
            logger.info("Runtime OpenAI API key updated")
        if item.key == "stripe_secret_key" and item.value:
            import os
            os.environ["STRIPE_SECRET_KEY"] = item.value
            logger.info("Runtime Stripe secret key updated")
        if item.key == "ai_providers_config" and item.value:
            import os
            try:
                providers = json.loads(item.value)
                env_map = {
                    "openai": "OPENAI_API_KEY",
                    "groq": "GROQ_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "azure": "AZURE_OPENAI_KEY",
                    "google": "GOOGLE_API_KEY",
                }
                for pid, pcfg in providers.items():
                    if pcfg.get("enabled") and pcfg.get("key") and pid in env_map:
                        os.environ[env_map[pid]] = pcfg["key"]
                        logger.info(f"Runtime {pid} API key updated")
            except Exception:
                pass

    audit_log(db, admin.id, admin.email, "settings.apply",
              details=f"Applied {len(results)} settings")
    return {"ok": True, "applied": len(results), "settings": results}


@router.post("/settings/test-provider")
def test_ai_provider(
    payload: dict,
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """Test connection to a specific AI provider. Payload: {provider_id, key, model}."""
    if not _is_super(admin):
        raise HTTPException(status_code=403, detail="Only super admin can test AI providers")
    import logging
    logger = logging.getLogger(__name__)
    provider_id = payload.get("provider_id", "")
    api_key = payload.get("key", "")
    model = payload.get("model", "")
    if not provider_id or not api_key:
        return {"ok": False, "error": "provider_id and key are required"}
    try:
        from app.ai.provider_client import test_connection
        test_connection(provider_id, {"key": api_key, "model": model})
        logger.info(f"Provider test OK: {provider_id}")
        return {"ok": True, "message": f"Connexion réussie avec {provider_id}!"}
    except Exception as e:
        logger.warning(f"Provider test FAILED: {provider_id}: {e}")
        return {"ok": False, "error": str(e)}


@router.put("/settings/token-limits")
def update_token_limits(
    limits: dict,
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """Update per-role token limits (JSON blob stored in PlatformSettings)."""
    from app.core.token_limits import update_token_limits as apply_limits
    result = apply_limits(admin.school_id, limits, db)
    return {"ok": True, "limits": result}


@router.get("/settings/token-limits")
def get_token_limits(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get current per-role token limits."""
    from app.core.token_limits import get_token_limits
    limits = get_token_limits(admin.school_id, db)
    return {"limits": limits}


@router.post("/settings/refresh-cache")
def refresh_settings_cache(
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """Force-invalidate the in-memory settings cache."""
    try:
        from app.services.settings_service import settings_cache
        settings_cache.invalidate(admin.school_id)
        return {"ok": True, "message": "Cache invalidated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# WALLET & FINANCE MANAGEMENT
# ============================================================

@router.get("/wallets")
def list_wallets(
    school_id: int | None = None,
    role: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get all user wallets with balances"""
    import logging
    logger = logging.getLogger(__name__)
    
    is_super = _is_super(admin)
    
    query = db.query(User)
    
    if not is_super:
        query = query.filter(User.school_id == admin.school_id)
    elif school_id:
        query = query.filter(User.school_id == school_id)
    
    if role:
        query = query.filter(User.role == role.upper())
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    school_ids = list(set(u.school_id for u in users))
    schools = {s.id: s.name for s in db.query(School).filter(School.id.in_(school_ids)).all()}

    user_ids = [u.id for u in users]
    totals = {}
    if user_ids:
        # SECURITY NOTE: This raw SQL is safe because `user_ids` comes from the ORM
        # query above, which is already filtered by school_id via the TenantMixin
        # event listener. If you modify this function, ensure the user_ids are still
        # school-scoped before passing them to this raw SQL query.
        rows = db.execute(
            text("""
                SELECT user_id,
                       COALESCE(SUM(CASE WHEN currency='DT' AND type::text IN ('dt_withdrawal','course_purchase','payout') THEN amount ELSE 0 END), 0) AS total_dt_spent,
                       COALESCE(SUM(CASE WHEN currency='TOKEN' AND type::text IN ('token_consumption','TOKEN_CONSUMPTION','course_purchase','COURSE_PURCHASE') THEN amount ELSE 0 END), 0) AS total_tokens_spent
                FROM transactions WHERE user_id = ANY(:ids) AND status='completed'
                GROUP BY user_id
            """),
            {"ids": user_ids},
        ).mappings()
        for row in rows:
            totals[row["user_id"]] = {
                "total_dt_spent": float(row["total_dt_spent"]),
                "total_tokens_spent": int(row["total_tokens_spent"]),
            }

    result = []
    for user in users:
        t = totals.get(user.id, {"total_dt_spent": 0.0, "total_tokens_spent": 0})
        result.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "school_id": user.school_id,
            "school_name": schools.get(user.school_id, "Unknown"),
            "balance_dt": user.dt_balance or 0.0,
            "balance_tokens": user.token_balance or 0,
            "total_dt_spent": t["total_dt_spent"],
            "total_tokens_spent": t["total_tokens_spent"],
            "is_active": user.is_active,
        })
    
    logger.warning(f"WALLET LIST: {len(result)} users returned, admin={admin.email}, is_super={is_super}")
    return {"total": total, "skip": skip, "limit": limit, "items": result}


class WalletAdjustRequest(BaseModel):
    amount_dt: float = 0
    amount_tokens: int = 0
    reason: str = "Manual adjustment by admin"


@router.post("/wallets/{user_id}/add")
def add_to_wallet(
    user_id: int,
    body: WalletAdjustRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """Add DT or tokens to user wallet"""
    import logging
    logger = logging.getLogger(__name__)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_super = _is_super(admin)

    if not is_super and user.school_id != admin.school_id:
        raise HTTPException(status_code=403, detail="Cannot modify other school users")

    old_dt = user.dt_balance or 0.0
    old_tokens = user.token_balance or 0
    new_dt = old_dt
    new_tokens = old_tokens

    if body.amount_dt > 0:
        user.dt_balance = old_dt + body.amount_dt
        new_dt = user.dt_balance
        tx = Transaction(
            school_id=user.school_id, user_id=user.id,
            type=TransactionType.DT_DEPOSIT, amount=body.amount_dt,
            currency="DT", description=body.reason, status="completed",
        )
        db.add(tx)

    if body.amount_tokens > 0:
        user.token_balance = old_tokens + body.amount_tokens
        new_tokens = user.token_balance
        tx = Transaction(
            school_id=user.school_id, user_id=user.id,
            type=TransactionType.TOKEN_RECHARGE, amount=body.amount_tokens,
            currency="TOKEN", description=body.reason, status="completed",
        )
        db.add(tx)

    db.commit()
    db.refresh(user)

    audit_log(db, admin.id, admin.email or "admin",
        "USER_BALANCE_ADJUST", target_type="user", target_id=user_id,
        details=f"add dt={body.amount_dt} tokens={body.amount_tokens} reason='{body.reason}'")

    logger.warning(
        f"WALLET ADD: user_id={user_id}, admin_id={admin.id}, "
        f"dt={old_dt}->{new_dt} (+{body.amount_dt}), tokens={old_tokens}->{new_tokens} (+{body.amount_tokens}), "
        f"reason='{body.reason}'"
    )

    return {
        "id": user.id,
        "email": user.email,
        "balance_dt": new_dt,
        "balance_tokens": new_tokens,
        "action": "add",
        "amount_dt": body.amount_dt,
        "amount_tokens": body.amount_tokens,
        "reason": body.reason,
        "admin_id": admin.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/wallets/{user_id}/deduct")
def deduct_from_wallet(
    user_id: int,
    body: WalletAdjustRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """Deduct DT or tokens from user wallet"""
    import logging
    logger = logging.getLogger(__name__)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_super = _is_super(admin)

    if not is_super and user.school_id != admin.school_id:
        raise HTTPException(status_code=403, detail="Cannot modify other school users")

    current_dt = user.dt_balance or 0.0
    current_tokens = user.token_balance or 0
    new_dt = current_dt
    new_tokens = current_tokens

    if body.amount_dt > 0:
        if body.amount_dt > current_dt:
            raise HTTPException(status_code=400, detail="Insufficient DT balance")
        user.dt_balance = current_dt - body.amount_dt
        new_dt = user.dt_balance
        tx = Transaction(
            school_id=user.school_id, user_id=user.id,
            type=TransactionType.DT_WITHDRAWAL, amount=body.amount_dt,
            currency="DT", description=body.reason, status="completed",
        )
        db.add(tx)

    if body.amount_tokens > 0:
        if body.amount_tokens > current_tokens:
            raise HTTPException(status_code=400, detail="Insufficient token balance")
        user.token_balance = current_tokens - body.amount_tokens
        new_tokens = user.token_balance
        tx = Transaction(
            school_id=user.school_id, user_id=user.id,
            type=TransactionType.TOKEN_CONSUMPTION, amount=body.amount_tokens,
            currency="TOKEN", description=body.reason, status="completed",
        )
        db.add(tx)

    db.commit()
    db.refresh(user)

    audit_log(db, admin.id, admin.email or "admin",
        "USER_BALANCE_ADJUST", target_type="user", target_id=user_id,
        details=f"deduct dt={body.amount_dt} tokens={body.amount_tokens} reason='{body.reason}'")

    logger.warning(
        f"WALLET DEDUCT: user_id={user_id}, admin_id={admin.id}, "
        f"dt={current_dt}->{new_dt} (-{body.amount_dt}), tokens={current_tokens}->{new_tokens} (-{body.amount_tokens}), "
        f"reason='{body.reason}'"
    )

    return {
        "id": user.id,
        "email": user.email,
        "balance_dt": new_dt,
        "balance_tokens": new_tokens,
        "action": "deduct",
        "amount_dt": body.amount_dt,
        "amount_tokens": body.amount_tokens,
        "reason": body.reason,
        "admin_id": admin.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stats/global")
def global_stats(db: Session = Depends(get_db), admin=Depends(require_platform_admin)):
    """Global platform statistics"""
    import logging
    from app.models import Transaction
    from sqlalchemy import func
    
    logger = logging.getLogger(__name__)
    
    is_super = _is_super(admin)
    
    if not is_super:
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    # User stats
    total_users = db.query(User).count()
    total_active = db.query(User).filter(User.is_active == True).count()
    total_teachers = db.query(User).filter(User.role.in_(["teacher"])).count()
    total_students = db.query(User).filter(User.role.in_(["student"])).count()
    total_admins = db.query(User).filter(User.role.in_(["admin_school", "super_admin"])).count()
    
    # School counts
    total_schools = db.query(School).count()
    active_schools = db.query(School).filter(School.is_active == True).count()
    
    # Financial stats
    total_dt_balances = db.query(func.sum(User.dt_balance)).scalar() or 0.0
    total_token_balances = db.query(func.sum(User.token_balance)).scalar() or 0
    
    # Transaction stats
    total_transactions = db.query(Transaction).count()
    total_dt_volume = db.query(func.sum(Transaction.amount)).filter(Transaction.currency == "DT").scalar() or 0.0
    
    # AI token consumption (OpenAI/Claude)
    from app.models import TransactionType
    ai_consumption = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type.in_([TransactionType.TOKEN_CONSUMPTION, "TOKEN_CONSUMPTION"]),
        Transaction.currency == "TOKEN",
        Transaction.status == "completed",
    ).scalar() or 0

    # Course stats
    total_courses = db.query(Course).count()
    published_courses = db.query(Course).filter(Course.is_published == True).count()
    
    # Subscription tiers
    tier_counts = {}
    for tier in ["free", "teacher_pro", "school", "institution"]:
        count = db.query(School).filter(School.subscription_tier == tier).count()
        tier_counts[tier] = count
    
    logger.warning(f"GLOBAL STATS: admin_id={admin.id}, total_users={total_users}, total_schools={total_schools}")
    
    return {
        "users": {
            "total": total_users,
            "active": total_active,
            "teachers": total_teachers,
            "students": total_students,
            "admins": total_admins,
        },
        "schools": {
            "total": total_schools,
            "active": active_schools,
            "by_tier": tier_counts,
        },
        "finances": {
            "total_dt_in_system": total_dt_balances,
            "total_tokens_in_system": total_token_balances,
            "total_transactions": total_transactions,
            "total_dt_volume": total_dt_volume,
        },
        "ai": {
            "total_tokens_consumed": int(ai_consumption),
            "estimated_cost_dt": round(float(ai_consumption) * 0.01, 2),
        },
        "courses": {
            "total": total_courses,
            "published": published_courses,
        },
    }


# ---- DELETE User ----

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin=Depends(require_platform_admin)):
    if _is_super(admin):
        user = db.query(User).filter(User.id == user_id).first()
    else:
        user = db.query(User).filter(User.id == user_id, User.school_id == admin.school_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_email = user.email
    db.delete(user)
    db.commit()

    audit_log(db, admin.id, admin.email or "unknown", "user.delete",
        target_type="user", target_id=user_id,
        details=f"deleted user {user_email}")

    return {"ok": True, "deleted": user_id}


# ---- Transactions ----

@router.get("/transactions")
def list_transactions(
    skip: int = 0,
    limit: int = 50,
    user_id: int | None = None,
    type: str | None = None,
    status: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str = Query("created_at", pattern="^(created_at|amount|type)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    query = db.query(Transaction)
    if _is_super(admin):
        pass
    else:
        query = query.filter(Transaction.school_id == admin.school_id)
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if type:
        try:
            type_enum = TransactionType(type)
            query = query.filter(Transaction.type == type_enum)
        except ValueError:
            pass
    if status:
        query = query.filter(Transaction.status == status)
    if search:
        st = f"%{search}%"
        from app.models import User as UModel
        query = query.join(UModel, Transaction.user_id == UModel.id).filter(
            (UModel.full_name.ilike(st)) | (UModel.email.ilike(st)) | (Transaction.description.ilike(st))
        )
    if date_from:
        query = query.filter(Transaction.created_at >= date_from)
    if date_to:
        query = query.filter(Transaction.created_at <= date_to)

    total = query.count()
    sort_col = {"created_at": Transaction.created_at, "amount": Transaction.amount, "type": Transaction.type}.get(sort_by, Transaction.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    transactions = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": t.id,
                "user_id": t.user_id,
                "user_email": t.user.email if t.user else None,
                "user_name": t.user.full_name if t.user else None,
                "type": t.type.value if hasattr(t.type, 'value') else str(t.type),
                "amount": t.amount,
                "currency": t.currency,
                "status": t.status,
                "description": t.description,
                "created_at": t.created_at,
            }
            for t in transactions
        ],
    }


# ---- Revenue Analytics ----

@router.get("/analytics/revenue")
def revenue_analytics(
    period: str = "30d",
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    from datetime import timedelta
    from dateutil.relativedelta import relativedelta

    now = datetime.now(timezone.utc)
    if period == "7d":
        start_date = now - timedelta(days=7)
    elif period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    elif period == "12m":
        start_date = now - relativedelta(months=12)
    else:
        start_date = now - timedelta(days=30)

    if _is_super(admin):
        transactions = db.query(Transaction).filter(
            Transaction.created_at >= start_date,
            Transaction.status == "completed",
        ).all()
        schools_q = db.query(School).all()
        users_q = db.query(User).all()
        courses_q = db.query(Course).all()
    else:
        transactions = db.query(Transaction).filter(
            Transaction.school_id == admin.school_id,
            Transaction.created_at >= start_date,
            Transaction.status == "completed",
        ).all()
        schools_q = db.query(School).filter(School.id == admin.school_id).all()
        users_q = db.query(User).filter(User.school_id == admin.school_id).all()
        courses_q = db.query(Course).filter(Course.school_id == admin.school_id).all()

    # Revenue by currency
    revenue_by_currency = {}
    for t in transactions:
        curr = t.currency or "DT"
        revenue_by_currency[curr] = revenue_by_currency.get(curr, 0) + t.amount

    # Active users in period
    active_user_ids = set(t.user_id for t in transactions if t.user_id)
    active_users = len(active_user_ids)
    total_users = len(users_q)
    conversion = round((active_users / total_users) * 100, 2) if total_users > 0 else 0

    # MRR/ARR approximation (monthly revenue)
    days_in_period = (now - start_date).days or 1
    monthly_revenue = sum(revenue_by_currency.values()) * (30 / days_in_period)
    arr = monthly_revenue * 12

    # AI cost estimate (token consumption)
    ai_cost_estimate = sum(t.amount for t in transactions if hasattr(t.type, 'value') and t.type.value in ["token_consumption", "ai_usage"]) * 0.01
    profit = sum(revenue_by_currency.values()) - ai_cost_estimate

    # Top schools by revenue
    school_revenues = {}
    for t in transactions:
        if t.user and t.user.school_id:
            school_revenues[t.user.school_id] = school_revenues.get(t.user.school_id, 0) + t.amount
    top_schools = sorted(school_revenues.items(), key=lambda x: x[1], reverse=True)[:5]
    top_schools_data = []
    for sid, rev in top_schools:
        school = db.query(School).filter(School.id == sid).first()
        top_schools_data.append({
            "school_id": sid,
            "school_name": school.name if school else f"School {sid}",
            "revenue": round(rev, 2),
        })

    # Course stats
    total_courses_count = len(courses_q)
    published_courses_count = sum(1 for c in courses_q if c.is_published) if hasattr(courses_q, '__iter__') else 0

    # Plan distribution (for super admin)
    plan_distribution = {}
    if _is_super(admin):
        for tier in ["free", "teacher_pro", "school", "institution"]:
            plan_distribution[tier] = db.query(School).filter(School.subscription_tier == tier).count()

    return {
        "period": period,
        "total_revenue": round(sum(revenue_by_currency.values()), 2),
        "revenue_by_currency": revenue_by_currency,
        "monthly_recurring_revenue": round(monthly_revenue, 2),
        "annual_run_rate": round(arr, 2),
        "ai_cost_estimate": round(ai_cost_estimate, 2),
        "estimated_profit": round(profit, 2),
        "active_users_in_period": active_users,
        "total_users": total_users,
        "conversion_rate": conversion,
        "top_schools": top_schools_data,
        "plan_distribution": plan_distribution,
        "total_transactions": len(transactions),
        "total_courses": total_courses_count,
        "published_courses": published_courses_count,
    }


# ---- Time-Series Analytics ----

@router.get("/analytics/enrollments")
def enrollment_trends(
    period: str = "30d",
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Daily new user registrations for charting."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    start = now - timedelta(days=days)

    school_filter = ""
    params = {"start": start}
    if not _is_super(admin):
        school_filter = "AND school_id = :school_id"
        params["school_id"] = admin.school_id

    rows = db.execute(
        text(f"""
            SELECT DATE(created_at) AS day, COUNT(*) AS count
            FROM users
            WHERE created_at >= :start {school_filter}
            GROUP BY DATE(created_at)
            ORDER BY day
        """),
        params,
    ).mappings()

    # Pad missing days with 0
    from collections import defaultdict
    counts = defaultdict(int)
    for row in rows:
        counts[str(row["day"])] = row["count"]

    result = []
    for i in range(days):
        day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({"date": day, "registrations": counts.get(day, 0)})

    return {"period": period, "data": result}


@router.get("/analytics/api-costs")
def api_cost_trends(
    period: str = "30d",
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Daily AI token consumption costs for charting."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    days = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}.get(period, 30)
    start = now - timedelta(days=days)

    school_filter = ""
    params = {"start": start}
    if not _is_super(admin):
        school_filter = "AND school_id = :school_id"
        params["school_id"] = admin.school_id

    rows = db.execute(
        text(f"""
            SELECT DATE(created_at) AS day,
                   COALESCE(SUM(amount), 0) AS tokens_consumed
            FROM transactions
            WHERE type::text IN ('token_consumption','TOKEN_CONSUMPTION')
              AND currency = 'TOKEN'
              AND status = 'completed'
              AND created_at >= :start {school_filter}
            GROUP BY DATE(created_at)
            ORDER BY day
        """),
        params,
    ).mappings()

    from collections import defaultdict
    counts = defaultdict(float)
    for row in rows:
        counts[str(row["day"])] = float(row["tokens_consumed"])

    result = []
    for i in range(days):
        day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        tokens = counts.get(day, 0)
        result.append({
            "date": day,
            "tokens_consumed": int(tokens),
            "estimated_cost_dt": round(tokens * 0.01, 2),
        })

    return {"period": period, "data": result}


# ---- Teacher Registrations ----

@router.get("/teacher-registrations")
def list_teacher_registrations(
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    query = db.query(TeacherRegistration)
    if not _is_super(admin):
        query = query.filter(TeacherRegistration.school_id == admin.school_id)
    if status_filter:
        query = query.filter(TeacherRegistration.status == status_filter)
    total = query.count()
    registrations = query.order_by(TeacherRegistration.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for r in registrations:
        result.append({
            "id": r.id,
            "email": r.email,
            "full_name": r.full_name,
            "status": r.status,
            "school_id": r.school_id,
            "rejection_reason": r.rejection_reason,
            "created_at": r.created_at,
            "reviewed_at": r.reviewed_at,
        })
    return {"total": total, "skip": skip, "limit": limit, "items": result}


@router.post("/teacher-registrations/{reg_id}/review")
def review_teacher_registration(
    reg_id: int,
    status: str,
    rejection_reason: str | None = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    from app.models import TeacherRegistration, SubscriptionPlan
    reg = db.query(TeacherRegistration).filter(TeacherRegistration.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    if not _is_super(admin) and reg.school_id != admin.school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    reg.status = status
    reg.reviewed_by = admin.id
    reg.reviewed_at = datetime.now(timezone.utc)
    if status == "rejected" and rejection_reason:
        reg.rejection_reason = rejection_reason
    
    if status == "approved":
        # Check school quota
        school = db.query(School).filter(School.id == reg.school_id).first()
        if school:
            max_users = school.max_users if school.max_users else 10
            current_count = db.query(User).filter(User.school_id == reg.school_id).count()
            if current_count >= max_users:
                raise HTTPException(status_code=400, detail=f"User limit reached ({max_users}). Cannot approve more teachers for this school.")

        # Find the user to update — prefer existing_user_id, fallback to email lookup
        user = None
        if reg.existing_user_id:
            user = db.query(User).filter(User.id == reg.existing_user_id).first()
        if not user:
            user = db.query(User).filter(User.email == reg.email).first()

        if user:
            user.role = UserRole.TEACHER
            user.is_approved = True
            user.school_id = reg.school_id
            user.subscription_plan = SubscriptionPlan.SCHOOL_AFFILIATED
            user.is_demo_account = False
        else:
            # No existing user — create one from the registration data
            if not reg.hashed_password:
                raise HTTPException(status_code=400, detail="Registration missing password data. Cannot create user account.")
            user = User(
                email=reg.email,
                full_name=reg.full_name,
                hashed_password=reg.hashed_password,
                role=UserRole.TEACHER,
                school_id=reg.school_id,
                subscription_plan=SubscriptionPlan.SCHOOL_AFFILIATED,
                is_active=True,
                is_approved=True,
            )
            db.add(user)
            db.flush()
            reg.existing_user_id = user.id

    db.commit()
    db.refresh(reg)

    audit_log(db, admin.id, admin.email or "unknown",
        f"registration.{status}",
        target_type="teacher_registration", target_id=reg_id,
        details=f"reviewed teacher registration for {reg.email}: {status}")

    return {"ok": True, "status": status, "reg_id": reg_id}


@router.post("/teacher/duplicate-trial-content")
def duplicate_trial_content(
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """Duplicate courses/chapters/lessons created during trial into the admin's real school.

    Only usable after a trial teacher has been approved and converted.
    Copies all courses authored by trial teachers in the demo school into
    the current admin's school, preserving structure.
    """
    from app.models import Course, Module, Lesson, SubscriptionPlan

    # Find trial-originated courses: courses authored by users who were
    # originally in the demo school (is_demo_account may now be False after conversion)
    demo_school = db.query(School).filter(School.school_type == SchoolType.DEMO).first()
    if not demo_school:
        raise HTTPException(status_code=404, detail="Demo school not found")

    trial_courses = db.query(Course).filter(Course.school_id == demo_school.id).all()
    if not trial_courses:
        return {"ok": True, "duplicated": 0, "message": "No trial courses to duplicate"}

    duplicated = 0
    for src_course in trial_courses:
        new_course = Course(
            school_id=admin.school_id,
            author_id=admin.id,
            title=src_course.title,
            description=src_course.description,
            short_description=src_course.short_description,
            thumbnail_url=src_course.thumbnail_url,
            category=src_course.category,
            level=src_course.level,
            language=src_course.language,
            prerequisites=src_course.prerequisites,
            learning_objectives=src_course.learning_objectives,
            tags=src_course.tags,
            status="draft",
            is_published=False,
        )
        db.add(new_course)
        db.flush()

        # Duplicate modules (chapters)
        src_modules = db.query(Module).filter(Module.course_id == src_course.id).order_by(Module.order).all()
        for src_mod in src_modules:
            new_mod = Module(
                course_id=new_course.id,
                title=src_mod.title,
                description=src_mod.description,
                order=src_mod.order,
            )
            db.add(new_mod)
            db.flush()

            # Duplicate lessons
            src_lessons = db.query(Lesson).filter(Lesson.module_id == src_mod.id).order_by(Lesson.order).all()
            for src_lesson in src_lessons:
                new_lesson = Lesson(
                    module_id=new_mod.id,
                    school_id=admin.school_id,
                    teacher_id=admin.id,
                    title=src_lesson.title,
                    description=src_lesson.description,
                    lesson_type=src_lesson.lesson_type,
                    content_text=src_lesson.content_text,
                    content_url=src_lesson.content_url,
                    video_url=src_lesson.video_url,
                    pdf_url=src_lesson.pdf_url,
                    document_url=src_lesson.document_url,
                    document_type=src_lesson.document_type,
                    image_urls=src_lesson.image_urls,
                    link_url=src_lesson.link_url,
                    link_title=src_lesson.link_title,
                    order=src_lesson.order,
                    duration_minutes=src_lesson.duration_minutes,
                    is_free=src_lesson.is_free,
                )
                db.add(new_lesson)

        duplicated += 1

    db.commit()

    audit_log(db, admin.id, admin.email or "unknown", "trial_content.duplicated",
              target_type="course", details=f"Duplicated {duplicated} courses from demo school")

    return {"ok": True, "duplicated": duplicated}


# ---- Identity Verification Review (super_admin only) ----

@router.get("/verifications/pending")
def list_pending_verifications(
    db: Session = Depends(get_db),
    admin=Depends(require_super_admin),
):
    """List all users with pending identity verification."""
    from app.models import VerificationStatus
    users = db.query(User).filter(User.verification_status == VerificationStatus.PENDING).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "subscription_plan": u.subscription_plan,
            "verification_document_url": u.verification_document_url,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.post("/verifications/{user_id}/review")
def review_verification(
    user_id: int,
    decision: str,
    rejection_reason: str | None = None,
    db: Session = Depends(get_db),
    admin=Depends(require_super_admin),
):
    """Approve or reject an identity verification. Never blocks platform usage."""
    from app.models import VerificationStatus
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if decision not in ("verified", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be 'verified' or 'rejected'")

    user.verification_status = decision
    user.verification_reviewed_by = admin.id
    user.verification_reviewed_at = datetime.now(timezone.utc)
    if decision == "rejected" and rejection_reason:
        user.verification_rejection_reason = rejection_reason
    db.commit()

    audit_log(db, admin.id, admin.email or "unknown", f"verification.{decision}",
              target_type="user", target_id=user_id,
              details=f"Verification {decision} for {user.email}")

    return {"ok": True, "status": decision, "user_id": user_id}


# ---- Schools CRUD ----

@router.delete("/schools/{school_id}")
def delete_school(school_id: int, db: Session = Depends(get_db), admin=Depends(require_platform_admin)):
    if not _is_super(admin):
        raise HTTPException(status_code=403, detail="Only super admin can delete schools")
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    db.delete(school)
    db.commit()
    return {"ok": True, "deleted": school_id}


# ---- Course Analytics ----

@router.get("/courses/{course_id}/analytics")
def course_analytics(course_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not _is_super(admin) and course.school_id != admin.school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    modules = db.query(Module).filter(Module.course_id == course_id).all()
    module_ids = [m.id for m in modules]
    lessons = db.query(Lesson).filter(Lesson.module_id.in_(module_ids)).all() if module_ids else []
    lesson_ids = [l.id for l in lessons]
    
    total_students = db.query(CoursePurchase).filter(CoursePurchase.course_id == course_id).count()
    total_revenue = db.query(func.sum(CoursePurchase.amount_paid)).filter(CoursePurchase.course_id == course_id).scalar() or 0.0
    
    progress_count = 0
    if lesson_ids:
        progress_count = db.query(LessonProgress).filter(LessonProgress.lesson_id.in_(lesson_ids)).count()
    
    return {
        "course_id": course_id,
        "course_title": course.title,
        "total_modules": len(modules),
        "total_lessons": len(lessons),
        "total_enrolled": total_students,
        "completion_rate": round((progress_count / (total_students * len(lessons)) * 100), 2) if total_students > 0 and len(lessons) > 0 else 0,
        "total_revenue": float(total_revenue),
    }


# ---- Audit Logs ----

@router.get("/audit-logs")
def list_audit_logs(
    action: str | None = None,
    admin_id: int | None = None,
    target_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    from app.models import AuditLog
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if admin_id:
        query = query.filter(AuditLog.admin_id == admin_id)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "page": page, "per_page": per_page, "items": [
        {
            "id": log.id,
            "admin_id": log.admin_id,
            "admin_email": log.admin_email,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at,
        }
        for log in logs
    ]}


# ---- Subscription Expiration Management (super_admin only) ----

@router.get("/subscriptions/expiring")
def list_expiring_subscriptions(
    days: int = 7,
    db: Session = Depends(get_db),
    admin=Depends(require_super_admin),
):
    """List independent_paid users whose subscription expires within N days."""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) + timedelta(days=days)
    users = db.query(User).filter(
        User.subscription_plan == "independent_paid",
        User.subscription_expires_at != None,
        User.subscription_expires_at <= cutoff,
    ).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "subscription_expires_at": u.subscription_expires_at.isoformat() if u.subscription_expires_at else None,
            "days_left": (u.subscription_expires_at - datetime.now(timezone.utc)).days if u.subscription_expires_at else None,
        }
        for u in users
    ]


@router.post("/subscriptions/check-expirations")
def trigger_expiration_check(
    admin=Depends(require_super_admin),
):
    """Manually trigger subscription expiration check and downgrade."""
    from app.tasks.subscription_expiration import check_subscription_expirations
    check_subscription_expirations()
    return {"ok": True, "message": "Expiration check completed"}


@router.post("/users/{user_id}/extend-subscription")
def extend_subscription(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    admin=Depends(require_super_admin),
):
    """Extend a user's subscription by N days."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from datetime import timedelta
    now = datetime.now(timezone.utc)
    current_expiry = user.subscription_expires_at or now
    if current_expiry < now:
        current_expiry = now
    user.subscription_expires_at = current_expiry + timedelta(days=days)
    user.subscription_plan = "independent_paid"
    db.commit()

    audit_log(db, admin.id, admin.email or "unknown", "subscription.extend",
              target_type="user", target_id=user_id,
              details=f"Extended by {days} days")

    return {"ok": True, "new_expiry": user.subscription_expires_at.isoformat()}


# ---- Wallet Management ----

@router.post("/wallet/allocate")
def allocate_credits(
    user_ids: list[int],
    amount: int,
    expires_days: int = 90,
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """Allocate school credits to users. Admin_school can only allocate to their own school."""
    from app.services.wallet import add_credits
    from app.models import WalletPool

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    admin_role = get_user_role(admin)
    if admin_role not in ("admin_school", "super_admin"):
        raise HTTPException(status_code=403, detail="Only school admin or super admin can allocate")

    from datetime import timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days) if expires_days > 0 else None
    allocated = []

    for uid in user_ids:
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            continue
        # School admins can only allocate within their own school
        if admin_role == "admin_school" and user.school_id != admin.school_id:
            continue
        tx = add_credits(db, uid, WalletPool.SCHOOL_ALLOCATED, amount, expires_at=expires_at)
        allocated.append(uid)

    audit_log(db, admin.id, admin.email or "unknown", "wallet.allocate",
              target_type="school", target_id=admin.school_id or 0,
              details=f"Allocated {amount} credits to {len(allocated)} users, expires {expires_days}d")

    return {"ok": True, "allocated_count": len(allocated), "amount": amount}


@router.get("/wallet/consumption-report")
def consumption_report(
    days: int = 30,
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """Credit consumption report for the admin's school."""
    from app.models import WalletTransaction, BillableFeature
    from datetime import timedelta
    from sqlalchemy import func

    admin_role = get_user_role(admin)
    if admin_role not in ("admin_school", "super_admin"):
        raise HTTPException(status_code=403, detail="Only school admin or super admin")

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Get users in this school
    from app.models import User as UserModel
    school_users = db.query(UserModel.id).filter(UserModel.school_id == admin.school_id)
    user_ids = [u.id for u in school_users]

    # Consumption per user per feature
    results = (
        db.query(
            WalletTransaction.user_id,
            WalletTransaction.feature,
            func.coalesce(func.sum(func.abs(WalletTransaction.amount)), 0),
        )
        .filter(
            WalletTransaction.user_id.in_(user_ids),
            WalletTransaction.amount < 0,  # debits only
            WalletTransaction.created_at >= cutoff,
        )
        .group_by(WalletTransaction.user_id, WalletTransaction.feature)
        .all()
    )

    report = {}
    for user_id, feature, total in results:
        if user_id not in report:
            report[user_id] = {}
        report[user_id][feature or "unknown"] = total

    return {"school_id": admin.school_id, "period_days": days, "consumption": report}


@router.get("/wallet/margin-report")
def margin_report(
    days: int = 30,
    db: Session = Depends(get_db),
    admin=Depends(require_super_admin),
):
    """Platform margin report: tokens consumed vs credits sold/allocated."""
    from app.models import AIUsageLog, WalletTransaction
    from datetime import timedelta
    from sqlalchemy import func

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Total tokens consumed (cost in USD from ai_usage_logs)
    token_stats = (
        db.query(
            func.coalesce(func.sum(AIUsageLog.tokens_used), 0),
            func.coalesce(func.sum(AIUsageLog.cost_usd), 0),
        )
        .filter(AIUsageLog.created_at >= cutoff)
        .first()
    )

    # Total credits consumed (debits)
    credits_consumed = (
        db.query(func.coalesce(func.sum(func.abs(WalletTransaction.amount)), 0))
        .filter(
            WalletTransaction.amount < 0,
            WalletTransaction.created_at >= cutoff,
        )
        .scalar()
    )

    # Total credits sold (purchased pool, positive)
    credits_sold = (
        db.query(func.coalesce(func.sum(WalletTransaction.amount), 0))
        .filter(
            WalletTransaction.pool == WalletPool.PURCHASED,
            WalletTransaction.amount > 0,
            WalletTransaction.created_at >= cutoff,
        )
        .scalar()
    )

    # Total credits allocated (school_allocated pool)
    credits_allocated = (
        db.query(func.coalesce(func.sum(WalletTransaction.amount), 0))
        .filter(
            WalletTransaction.pool == WalletPool.SCHOOL_ALLOCATED,
            WalletTransaction.amount > 0,
            WalletTransaction.created_at >= cutoff,
        )
        .scalar()
    )

    return {
        "period_days": days,
        "tokens_consumed": token_stats[0],
        "cost_usd": token_stats[1],
        "credits_consumed": credits_consumed,
        "credits_sold": credits_sold,
        "credits_allocated": credits_allocated,
    }


# ============================================================
# SCHOOL PACK PURCHASE
# ============================================================

@router.post("/school/packs/purchase")
def purchase_school_pack(
    body: dict,
    db: Session = Depends(get_db),
    admin=Depends(require_school_admin_strict),
):
    """
    Achat d'un pack pour l'école (admin_school ou super_admin).
    purchaser_type="school", couvre tous les élèves du niveau du pack.
    """
    from app.models import StudyPack, PackPurchase, PackStatus, PackPurchaseStatus, PurchaserType, User as UserModel
    from datetime import timedelta

    pack_id = body.get("pack_id")
    if not pack_id:
        raise HTTPException(status_code=400, detail="pack_id requis")

    # Vérifier le pack
    pack = db.query(StudyPack).filter(
        StudyPack.id == pack_id,
        StudyPack.status == PackStatus.PUBLISHED.value,
    ).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found or not published")

    # Vérifier que l'admin gère bien une école
    if not admin.school_id:
        raise HTTPException(status_code=400, detail="Vous n'êtes pas associé à une école")

    # Vérifier qu'un pack actif n'existe pas déjà pour ce niveau dans cette école
    now = datetime.now(timezone.utc)
    existing = db.query(PackPurchase).filter(
        PackPurchase.school_id == admin.school_id,
        PackPurchase.purchaser_type == PurchaserType.SCHOOL.value,
        PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
        PackPurchase.valid_until > now,
    ).join(StudyPack).filter(StudyPack.niveau_scolaire == pack.niveau_scolaire).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Un pack actif pour le niveau '{pack.niveau_scolaire}' existe déjà pour votre école (expire le {existing.valid_until.strftime('%d/%m/%Y')})."
        )

    # Débiter le solde de l'école (via le compte de l'admin)
    if admin.dt_balance < pack.price:
        raise HTTPException(
            status_code=400,
            detail=f"Solde insuffisant. Solde actuel: {admin.dt_balance} {pack.currency}, prix du pack: {pack.price} {pack.currency}"
        )

    admin.dt_balance -= pack.price

    # Créer la transaction
    transaction = Transaction(
        school_id=admin.school_id,
        user_id=admin.id,
        type=TransactionType.COURSE_PURCHASE,
        amount=pack.price,
        currency=Currency.DT,
        description=f"Achat pack école: {pack.name}",
        reference_id=f"pack_{pack_id}",
        status="completed",
    )
    db.add(transaction)

    # Créer l'achat de pack
    valid_from = now
    valid_until = now + timedelta(days=pack.validity_duration_days)

    purchase = PackPurchase(
        pack_id=pack_id,
        purchaser_type=PurchaserType.SCHOOL.value,
        student_id=None,
        school_id=admin.school_id,
        valid_from=valid_from,
        valid_until=valid_until,
        status=PackPurchaseStatus.ACTIVE.value,
        amount_paid=pack.price,
        currency=pack.currency,
        transaction_id=str(transaction.id),
    )
    db.add(purchase)

    # Compter les élèves du niveau concerné
    student_count = db.query(UserModel).filter(
        UserModel.school_id == admin.school_id,
        UserModel.role == "student",
        UserModel.niveau_scolaire == pack.niveau_scolaire,
        UserModel.is_active == True,
    ).count()

    db.commit()
    db.refresh(purchase)

    return {
        "id": purchase.id,
        "pack_id": purchase.pack_id,
        "pack_name": pack.name,
        "niveau_scolaire": pack.niveau_scolaire,
        "valid_from": valid_from.isoformat(),
        "valid_until": valid_until.isoformat(),
        "amount_paid": purchase.amount_paid,
        "currency": purchase.currency,
        "students_covered": student_count,
        "remaining_balance": admin.dt_balance,
        "message": f"Pack '{pack.name}' acheté pour l'école. {student_count} élève(s) du niveau '{pack.niveau_scolaire}' couvert(s) automatiquement."
    }


# ============================================================
# SCHOOL PACK DASHBOARD
# ============================================================

@router.get("/school/packs/active")
def list_active_school_packs(
    db: Session = Depends(get_db),
    admin=Depends(require_school_admin_strict),
):
    """
    Liste des packs actifs pour l'école de l'admin connecté.
    Inclut le nombre d'élèves du niveau concerné et une alerte d'expiration (J-30).
    """
    from app.models import StudyPack, PackPurchase, PackPurchaseStatus, PurchaserType, User as UserModel
    from datetime import timedelta

    if not admin.school_id:
        raise HTTPException(status_code=400, detail="Pas d'école associée")

    now = datetime.now(timezone.utc)
    alert_threshold = now + timedelta(days=30)

    active_purchases = db.query(PackPurchase).filter(
        PackPurchase.school_id == admin.school_id,
        PackPurchase.purchaser_type == PurchaserType.SCHOOL.value,
        PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
    ).all()

    result = []
    for purchase in active_purchases:
        pack = db.query(StudyPack).filter(StudyPack.id == purchase.pack_id).first()
        if not pack:
            continue

        student_count = db.query(UserModel).filter(
            UserModel.school_id == admin.school_id,
            UserModel.role == "student",
            UserModel.niveau_scolaire == pack.niveau_scolaire,
            UserModel.is_active == True,
        ).count()

        expiring_soon = purchase.valid_until <= alert_threshold

        result.append({
            "purchase_id": purchase.id,
            "pack_id": pack.id,
            "pack_name": pack.name,
            "niveau_scolaire": pack.niveau_scolaire,
            "valid_from": purchase.valid_from.isoformat(),
            "valid_until": purchase.valid_until.isoformat(),
            "students_covered": student_count,
            "days_remaining": max(0, (purchase.valid_until - now).days),
            "expiring_soon": expiring_soon,
        })

    return {
        "school_id": admin.school_id,
        "total_active": len(result),
        "packs": result,
    }


# ============================================================
# SUPER ADMIN — REVENUE REPORT
# ============================================================

@router.get("/packs/revenue-report")
def pack_revenue_report(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin=Depends(require_platform_admin),
):
    """
    Rapport de revenus : packs vs cours à l'unité.
    Comparaison sur les N derniers jours.
    """
    from app.models import PackPurchase, CoursePurchase, StudyPack
    from sqlalchemy import func

    if not _is_super(admin):
        raise HTTPException(status_code=403, detail="Réservé au super admin")

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Revenus packs individuels
    individual_pack_revenue = (
        db.query(func.coalesce(func.sum(PackPurchase.amount_paid), 0))
        .filter(
            PackPurchase.purchaser_type == "student",
            PackPurchase.created_at >= cutoff,
        )
        .scalar()
    )

    # Revenus packs école
    school_pack_revenue = (
        db.query(func.coalesce(func.sum(PackPurchase.amount_paid), 0))
        .filter(
            PackPurchase.purchaser_type == "school",
            PackPurchase.created_at >= cutoff,
        )
        .scalar()
    )

    # Revenus cours à l'unité
    course_unit_revenue = (
        db.query(func.coalesce(func.sum(CoursePurchase.amount_paid), 0))
        .filter(CoursePurchase.purchased_at >= cutoff)
        .scalar()
    )

    # Nombre d'achats
    individual_pack_count = db.query(PackPurchase).filter(
        PackPurchase.purchaser_type == "student",
        PackPurchase.created_at >= cutoff,
    ).count()

    school_pack_count = db.query(PackPurchase).filter(
        PackPurchase.purchaser_type == "school",
        PackPurchase.created_at >= cutoff,
    ).count()

    course_unit_count = db.query(CoursePurchase).filter(
        CoursePurchase.purchased_at >= cutoff,
    ).count()

    total_pack = float(individual_pack_revenue) + float(school_pack_revenue)
    total_all = total_pack + float(course_unit_revenue)

    return {
        "period_days": days,
        "packs_individuels": {
            "revenue": float(individual_pack_revenue),
            "count": individual_pack_count,
        },
        "packs_ecole": {
            "revenue": float(school_pack_revenue),
            "count": school_pack_count,
        },
        "cours_unite": {
            "revenue": float(course_unit_revenue),
            "count": course_unit_count,
        },
        "totals": {
            "packs": total_pack,
            "cours_unite": float(course_unit_revenue),
            "all": total_all,
        },
        "pack_vs_unit_ratio": round(total_pack / float(course_unit_revenue), 2) if course_unit_revenue else 0,
    }


# ── CSV Import ────────────────────────────────────────────────

@router.post("/import-students")
def import_students_from_csv(
    csv_content: str,
    db: Session = Depends(get_db),
    admin=Depends(require_school_admin_strict),
):
    """Import students from CSV text content.
    Expected CSV columns: email, full_name, password, niveau_scolaire (optional).
    First row is treated as header if it contains 'email'.
    """
    target_school_id = admin.school_id
    if not target_school_id:
        raise HTTPException(status_code=400, detail="No school associated with your account")

    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="Empty CSV file")

    # Detect header
    start_idx = 0
    if rows[0] and rows[0][0].strip().lower() == "email":
        start_idx = 1

    created = []
    errors = []

    for i, row in enumerate(rows[start_idx:], start=start_idx + 1):
        if len(row) < 3 or not row[0].strip():
            errors.append({"line": i, "error": "Missing required fields (email, full_name, password)"})
            continue

        email = row[0].strip()
        full_name = row[1].strip() if len(row) > 1 else ""
        password = row[2].strip() if len(row) > 2 else ""
        niveau = row[3].strip() if len(row) > 3 else None

        if not email or not password:
            errors.append({"line": i, "error": "Email and password are required"})
            continue

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            errors.append({"line": i, "error": f"Email '{email}' already registered"})
            continue

        ok, err = validate_password_strength(password)
        if not ok:
            errors.append({"line": i, "error": f"Weak password: {err}"})
            continue

        new_user = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role="student",
            school_id=target_school_id,
            niveau_scolaire=niveau if niveau else None,
            is_active=True,
            is_approved=True,
        )
        db.add(new_user)
        db.flush()

        # Grant trial credits
        from app.services.wallet import add_credits
        from datetime import timedelta
        add_credits(
            db, new_user.id, WalletPool.TRIAL, 100,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        created.append({"email": email, "full_name": full_name, "id": new_user.id})

    db.commit()

    return {
        "created": len(created),
        "errors": len(errors),
        "items_created": created,
        "items_errors": errors,
    }


@router.post("/import-students/upload")
async def import_students_upload(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    admin=Depends(require_school_admin_strict),
):
    """Import students from an uploaded CSV file."""
    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content.decode("latin-1")

    return import_students_from_csv(csv_text, db, admin)