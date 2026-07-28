"""Users API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.auth import get_current_user
from app.models import User, UserRole
from app.schemas import UserRead, UserBalanceUpdate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def require_teacher_or_admin(current_user: User = Depends(get_current_user)):
    allowed = {UserRole.TEACHER, UserRole.ADMIN_SCHOOL, UserRole.SUPER_ADMIN}
    if current_user.role not in allowed:
        raise HTTPException(status_code=403, detail="Teacher or admin access required")
    return current_user


def _require_admin(current_user: User = Depends(get_current_user)):
    admin_roles = {UserRole.ADMIN_SCHOOL, UserRole.SUPER_ADMIN, UserRole.PEDAGOGICAL_ADMIN, UserRole.PEDAGOGICAL_LEAD}
    if current_user.role not in admin_roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/me", response_model=UserRead)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.get("", response_model=List[UserRead])
def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """List users (teachers and admins only)"""
    query = db.query(User).filter(User.school_id == current_user.school_id)
    
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    return query.all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user by ID"""
    user = db.query(User).filter(
        User.id == user_id,
        User.school_id == current_user.school_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# PUT /{user_id}/balance removed — use /api/admin/users/{user_id}/balance instead


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    """Update user profile. Role changes restricted to admins only."""
    user = db.query(User).filter(
        User.id == user_id,
        User.school_id == current_user.school_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.role is not None:
        # Only admins can change roles
        admin_roles = {UserRole.ADMIN_SCHOOL, UserRole.SUPER_ADMIN}
        if current_user.role not in admin_roles:
            raise HTTPException(status_code=403, detail="Only admins can change user roles")
        # Non-super admins cannot assign super_admin
        if current_user.role != UserRole.SUPER_ADMIN and user_update.role == "super_admin":
            raise HTTPException(status_code=403, detail="Only super_admin can promote to super_admin")
        user.role = user_update.role
    
    db.commit()
    db.refresh(user)
    
    return user