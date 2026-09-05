"""Users API endpoints"""
from datetime import datetime
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


@router.put("/me", response_model=UserRead)
def update_current_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's own profile (niveau_scolaire, full_name, language)."""
    niveau_changed = (
        user_update.niveau_scolaire is not None
        and user_update.niveau_scolaire != current_user.niveau_scolaire
    )

    if user_update.niveau_scolaire is not None:
        current_user.niveau_scolaire = user_update.niveau_scolaire
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.language is not None:
        current_user.language = user_update.language

    # Invalider les abonnements dont le pack ne correspond plus au niveau,
    # puis garantir le contrat Freemium en re-créant un abonnement gratuit
    # actif sur le NOUVEAU niveau (sinon l'élève se retrouve sans AUCUN
    # abonnement actif → dashboard/mon-parcours vides).
    if niveau_changed and current_user.role == "student":
        from app.models import Abonnement, PackDefinition
        active_statuses = ("actif", "grace")
        abonnements = db.query(Abonnement).filter(
            Abonnement.user_id == current_user.id,
            Abonnement.statut.in_(active_statuses),
        ).all()
        invalidated = 0
        for abo in abonnements:
            pack = db.query(PackDefinition).filter(PackDefinition.id == abo.pack_id).first()
            if pack and pack.niveau_scolaire != current_user.niveau_scolaire:
                abo.statut = "invalide"
                abo.updated_at = datetime.utcnow()
                invalidated += 1
        # Garantie Freemium systématique : l'élève peut n'avoir AUCUN abonnement
        # actif avant le changement (ex: tout déjà invalidé) — on garantit alors
        # aussi le gratuit sur le nouveau niveau. No-op si un actif compatible existe.
        from app.services.student_tier import ensure_free_abonnement
        ensure_free_abonnement(current_user, db)

    db.commit()
    db.refresh(current_user)
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
    """Update user profile. Teachers may only edit their own account; is_active/role changes require admin_school or super_admin."""
    is_school_admin = current_user.role in {UserRole.ADMIN_SCHOOL, UserRole.SUPER_ADMIN}
    if current_user.role == UserRole.TEACHER and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Un enseignant ne peut modifier que son propre compte")
    if not is_school_admin and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only school admins can modify other users")

    user = db.query(User).filter(
        User.id == user_id,
        User.school_id == current_user.school_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    privileged_change = user_update.is_active is not None or user_update.role is not None
    if privileged_change and not is_school_admin:
        raise HTTPException(status_code=403, detail="Seuls les admins peuvent modifier is_active ou le rôle")

    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.role is not None:
        # Non-super admins cannot assign super_admin
        if current_user.role != UserRole.SUPER_ADMIN and user_update.role == "super_admin":
            raise HTTPException(status_code=403, detail="Only super_admin can promote to super_admin")
        user.role = user_update.role

    db.commit()
    db.refresh(user)

    return user