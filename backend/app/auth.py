import os
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.security import verify_password, get_password_hash
from app.core.config import get_settings
from app.core.validation import validate_password_strength
from app.audit import log_security_event
from app.schemas import Token, UserRead, UserCreate
from app.models import SubscriptionPlan, SchoolType, UserRole, User

settings = get_settings()

router = APIRouter()


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a short-lived access token (default: 30 minutes)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    """Create a long-lived refresh token (default: 7 days).

    The token itself is a JWT so the client can store it, but we ALSO
    store a hash in the RefreshToken table for server-side revocation.
    A UUID jti claim ensures every token is unique even for the same user.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _hash_token(token: str) -> str:
    """SHA-256 hash of the opaque token for DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_token_pair(user: User, db: Session) -> dict:
    """Generate access + refresh token pair and persist the refresh token.

    JWT payload now includes:
    - roles: full list of user roles (backward compat: falls back to [user.role])
    - active_role: the currently selected context role
    """
    # Backward compat: if user.roles is empty, use [user.role]
    user_roles = user.roles if user.roles else [user.role]
    active_role = user.active_context_role or user_roles[0]

    payload = {
        "sub": str(user.id),
        "school_id": user.school_id,
        "roles": user_roles,
        "active_role": active_role,
    }

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    # Persist refresh token hash for server-side revocation
    from app.models import RefreshToken
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days),
    ))
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _get_user_by_id(db: Session, user_id: int):
    from app.models import User
    return db.query(User).filter(User.id == user_id).first()


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: int = int(payload.get("sub"))
        token_type: str = payload.get("type", "access")
        if token_type != "access":
            raise credentials_exception
    except Exception:
        raise credentials_exception
    user = _get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    if user.is_active is False:
        log_security_event("account_disabled_access_attempt", {"user_id": user.id, "email": user.email}, severity="WARNING")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    # --- Apply active_role from JWT claim (context switcher support) ---
    active_role_claim = payload.get("active_role")
    if active_role_claim:
        user.active_context_role = active_role_claim

    # --- Impersonation detection (read-only flag for downstream use) ---
    impersonated_by = payload.get("impersonated_by")
    if impersonated_by:
        user._impersonated_by = impersonated_by

    # --- Multi-tenant context setup (SECURITY: second line of defense) ---
    from app.db import current_tenant_id, _tenant_filter_suppressed
    from app.deps import get_user_role
    role = get_user_role(user)
    if role in ("super_admin", "pedagogical_admin"):
        _tenant_filter_suppressed.set(True)
    else:
        school_id = getattr(user, "school_id", None)
        if school_id is not None:
            current_tenant_id.set(school_id)

    return user


# ---------------------------------------------------------------------------
# Registration endpoints
# ---------------------------------------------------------------------------

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    from app.models import User, School, SchoolType
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    school = None
    domain = user_in.school_domain or (user_in.school_name.lower().replace(" ", "-") if user_in.school_name else None)

    if domain:
        school = db.query(School).filter(School.domain == domain).first()

    if not school and user_in.school_name:
        slug = domain or user_in.school_name.lower().replace(" ", "-")
        existing_slug = db.query(School).filter(School.slug == slug).first()
        if existing_slug:
            slug = f"{slug}-{existing_slug.id}"
        school = School(name=user_in.school_name, domain=domain, slug=slug)
        db.add(school)
        db.flush()

    if not school:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School name is required. Please provide the name of your school.",
        )
    role = "student"
    ok, err = validate_password_strength(user_in.password)
    if not ok:
        raise HTTPException(status_code=422, detail=err)
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        school_id=school.id,
        hashed_password=get_password_hash(user_in.password),
        role=role,
        niveau_scolaire=user_in.niveau_scolaire,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    from app.services.wallet import add_credits
    from app.models import WalletPool
    add_credits(
        db, new_user.id, WalletPool.TRIAL, 100,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    return _issue_token_pair(new_user, db)


@router.post("/register-school", response_model=Token)
def register_school(body: "RegisterSchoolRequest", db: Session = Depends(get_db)):
    """Public school registration — creates a school with pending_validation=True."""
    from app.models import User, School, SchoolType, UserRole
    from app.schemas import RegisterSchoolRequest

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    ok, err = validate_password_strength(body.password)
    if not ok:
        raise HTTPException(status_code=422, detail=err)

    slug = (body.school_domain or body.school_name.lower().replace(" ", "-")).replace("'", "")
    existing_slug = db.query(School).filter(School.slug == slug).first()
    if existing_slug:
        slug = f"{slug}-{existing_slug.id}"

    school = School(
        name=body.school_name,
        slug=slug,
        domain=body.school_domain,
        school_type=SchoolType.REAL,
        is_active=False,
        pending_validation=True,
    )
    db.add(school)
    db.flush()

    new_user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=get_password_hash(body.password),
        role=UserRole.ADMIN_SCHOOL,
        school_id=school.id,
        is_active=True,
        is_approved=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.refresh(school)

    log_security_event("school_registration_pending", {
        "user_id": new_user.id,
        "email": new_user.email,
        "school_id": school.id,
        "school_name": school.name,
    })

    return _issue_token_pair(new_user, db)


@router.post("/register-trial-teacher", response_model=Token)
def register_trial_teacher(user_in: UserCreate, db: Session = Depends(get_db)):
    """Instant trial: creates a teacher account linked to the demo school."""
    from app.models import User, School

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    ok, err = validate_password_strength(user_in.password)
    if not ok:
        raise HTTPException(status_code=422, detail=err)

    demo_school = db.query(School).filter(School.school_type == SchoolType.DEMO).first()
    if not demo_school:
        raise HTTPException(status_code=500, detail="Demo school not configured. Please contact support.")

    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=UserRole.TEACHER,
        school_id=demo_school.id,
        subscription_plan=SubscriptionPlan.TRIAL,
        is_demo_account=True,
        is_active=True,
        is_approved=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    from app.services.wallet import add_credits
    from app.models import WalletPool
    add_credits(
        db, new_user.id, WalletPool.TRIAL, 100,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    log_security_event("trial_teacher_registered", {
        "user_id": new_user.id,
        "email": new_user.email,
        "school_id": demo_school.id,
    })

    return _issue_token_pair(new_user, db)


@router.post("/teacher-register")
def teacher_register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Public teacher registration — creates a pending TeacherRegistration request."""
    from app.models import User, School, TeacherRegistration, TeacherRegistrationStatus

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    ok, err = validate_password_strength(user_in.password)
    if not ok:
        raise HTTPException(status_code=422, detail=err)

    school = None
    if getattr(user_in, "school_id", None):
        school = db.query(School).filter(School.id == user_in.school_id).first()
    if not school and user_in.school_name:
        school = db.query(School).filter(School.name.ilike(user_in.school_name)).first()
    if not school:
        raise HTTPException(status_code=400, detail="École introuvable. Veuillez sélectionner une école dans la liste.")

    reg = TeacherRegistration(
        school_id=school.id,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        status=TeacherRegistrationStatus.PENDING,
    )
    db.add(reg)
    db.commit()

    return {"message": "Registration request submitted. You will receive an email once reviewed.", "school_name": school.name}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def _mask_email(email: str) -> str:
    """Mask email for safe logging: j***@example.com."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***" if local else "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    from app.models import User
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"LOGIN ATTEMPT: email={_mask_email(form_data.username)}")
    user = db.query(User).filter(User.email == form_data.username).first()
    logger.info(f"USER FOUND: user_id={user.id if user else 'None'}")

    if not user:
        log_security_event("failed_login", {"email": form_data.username}, severity="WARNING")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    # Account lockout check
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if user.locked_until and user.locked_until > now:
        remaining = (user.locked_until - now).seconds // 60 + 1
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to too many failed attempts. Try again in {remaining} min.",
        )

    if not verify_password(form_data.password, user.hashed_password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
            user.failed_login_attempts = 0
            log_security_event("account_locked", {"user_id": user.id, "email": _mask_email(user.email)}, severity="WARNING")
        db.commit()
        log_security_event("failed_login", {"email": _mask_email(form_data.username)}, severity="WARNING")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    # Successful login — reset lockout state
    user.failed_login_attempts = 0
    user.locked_until = None

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated. Contact your administrator.")

    # Initialize active_context_role from roles list (backward compat)
    user_roles = user.roles if user.roles else [user.role]
    if not user.active_context_role:
        user.active_context_role = user_roles[0]

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return _issue_token_pair(user, db)


# ---------------------------------------------------------------------------
# Context Switching
# ---------------------------------------------------------------------------

class SwitchContextRequest(BaseModel):
    role: str


@router.post("/switch-context", response_model=Token)
def switch_context(body: SwitchContextRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Switch the active context role for the current user.

    The requested role must be present in the user's roles list.
    Returns a new token pair with the updated active_role claim.
    """
    # Get user's full roles list (backward compat)
    user_roles = current_user.roles if current_user.roles else [current_user.role]

    if body.role not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{body.role}' not in your roles. Available: {user_roles}",
        )

    current_user.active_context_role = body.role
    db.commit()

    log_security_event("context_switched", {
        "user_id": current_user.id,
        "new_role": body.role,
    })

    return _issue_token_pair(current_user, db)


# ---------------------------------------------------------------------------
# Impersonation (Support / Super Admin)
# ---------------------------------------------------------------------------

@router.post("/impersonate/{target_user_id}")
def impersonate_user(
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Impersonate a target user. Restricted to support and super_admin roles.

    Creates an audit trail entry and returns a token for the target user
    with an impersonated_by claim.
    """
    from fastapi import Request
    from app.models import AuditImpersonation

    # Check authorization: support or super_admin role required
    user_roles = current_user.roles if current_user.roles else [current_user.role]
    if "support" not in user_roles and "super_admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Support or super_admin role required for impersonation",
        )

    # Cannot impersonate yourself
    if target_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot impersonate yourself",
        )

    target_user = _get_user_by_id(db, target_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    if not target_user.is_active:
        raise HTTPException(status_code=400, detail="Cannot impersonate an inactive user")

    # Create audit entry
    audit = AuditImpersonation(
        support_user_id=current_user.id,
        target_user_id=target_user_id,
        started_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()

    log_security_event("impersonation_started", {
        "support_user_id": current_user.id,
        "target_user_id": target_user_id,
    })

    # Generate token for target user with impersonated_by claim
    target_roles = target_user.roles if target_user.roles else [target_user.role]
    target_active_role = target_user.active_context_role or target_roles[0]

    payload = {
        "sub": str(target_user.id),
        "school_id": target_user.school_id,
        "roles": target_roles,
        "active_role": target_active_role,
        "impersonated_by": current_user.id,
    }

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "impersonated_by": current_user.id,
        "target_user": {
            "id": target_user.id,
            "email": target_user.email,
            "full_name": target_user.full_name,
            "role": target_user.role,
        },
    }


@router.post("/impersonate/stop")
def stop_impersonation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stop the active impersonation session and return a fresh token for the support user."""
    from app.models import AuditImpersonation

    # Find the active impersonation session for this support user
    session = db.query(AuditImpersonation).filter(
        AuditImpersonation.support_user_id == current_user.id,
        AuditImpersonation.ended_at.is_(None),
    ).order_by(AuditImpersonation.started_at.desc()).first()

    if session:
        session.ended_at = datetime.now(timezone.utc)
        db.commit()

        log_security_event("impersonation_stopped", {
            "support_user_id": current_user.id,
            "target_user_id": session.target_user_id,
        })

    # Return a fresh token for the support user (resets to their own context)
    return _issue_token_pair(current_user, db)


# ---------------------------------------------------------------------------
# Refresh Token
# ---------------------------------------------------------------------------

class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh-token", response_model=Token)
def refresh_token(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access+refresh token pair.

    Implements refresh token rotation: the old refresh token is invalidated
    and a new pair is issued.  This limits the damage of a leaked token.
    """
    from app.models import RefreshToken

    # 1. Decode the JWT to get user_id (validate expiry & signature)
    try:
        payload = jwt.decode(body.refresh_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # 2. Look up the refresh token hash in DB
    token_hash = _hash_token(body.refresh_token)
    stored = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
    ).first()

    if not stored:
        # Possible token reuse attack — revoke ALL tokens for this user
        log_security_event("refresh_token_reuse_detected", {
            "user_id": user_id,
        }, severity="WARNING")
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update({"revoked": True})
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token already used or revoked")

    # 3. Revoke the old refresh token (rotation)
    stored.revoked = True
    db.commit()

    # 4. Issue a new pair
    user = _get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return _issue_token_pair(user, db)


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me/language")
def update_language(language: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if language not in ("fr", "en", "ar"):
        raise HTTPException(status_code=400, detail="Language must be fr, en, or ar")
    current_user.language = language
    db.commit()
    return {"language": language}


@router.put("/me/onboarding-complete")
def complete_onboarding(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.onboarding_complete = True
    db.commit()
    return {"onboarding_complete": True}


@router.get("/schools/search")
def search_schools(q: str = "", db: Session = Depends(get_db)):
    from app.models import School
    query = db.query(School).filter(School.is_active == True)
    if q.strip():
        query = query.filter(School.name.ilike(f"%{q}%"))
    schools = query.order_by(School.name).limit(10).all()
    return [{"id": s.id, "name": s.name, "slug": s.slug} for s in schools]


@router.get("/schools/join/{code}")
def join_school_by_code(code: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import School
    school = db.query(School).filter(School.invite_code == code, School.is_active == True).first()
    if not school:
        raise HTTPException(status_code=404, detail="Invalid or inactive invitation code")
    current_user.school_id = school.id
    db.commit()
    return {"school_id": school.id, "school_name": school.name}


# ---------------------------------------------------------------------------
# Password Reset Flow (Forgot / Reset)
# ---------------------------------------------------------------------------

import secrets as _secrets


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Generate a secure reset token and save it to DB with 1-hour expiry.

    Always returns 200 to prevent email enumeration.
    """
    from app.models import User, PasswordResetToken

    user = db.query(User).filter(User.email == body.email).first()

    if user:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
        ).update({"used": True})

        reset_token = _secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        db.add(PasswordResetToken(
            user_id=user.id,
            school_id=user.school_id,
            token=reset_token,
            expires_at=expires_at,
        ))
        db.commit()

        log_security_event("password_reset_requested", {
            "user_id": user.id,
            "email": user.email,
        })

        # Send reset email (failures logged server-side, never exposed to client)
        from app.services.email_service import send_password_reset_email
        send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token,
            user_name=user.full_name,
        )

        return {
            "message": "Si cet email est enregistré, vous recevrez un lien de réinitialisation.",
        }

    return {"message": "Si cet email est enregistré, vous recevrez un lien de réinitialisation."}


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a valid, non-expired, non-used token."""
    from app.models import User, PasswordResetToken

    now = datetime.now(timezone.utc)
    reset_entry = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == body.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > now,
    ).first()

    if not reset_entry:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré.")

    ok, err = validate_password_strength(body.new_password)
    if not ok:
        raise HTTPException(status_code=422, detail=err)

    user = db.query(User).filter(User.id == reset_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Utilisateur introuvable.")

    user.hashed_password = get_password_hash(body.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None

    reset_entry.used = True
    db.commit()

    log_security_event("password_reset_completed", {
        "user_id": user.id,
        "email": user.email,
    })

    return {"message": "Mot de passe réinitialisé avec succès."}
