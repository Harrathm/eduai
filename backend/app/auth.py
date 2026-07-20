import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
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

# Local in-file helper to create token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


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
    return user


@router.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    from app.models import User, School
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    domain = user_in.school_domain or (user_in.school_name.lower().replace(" ", "-") if user_in.school_name else None)
    if domain:
        school = db.query(School).filter(School.domain == domain).first()
    else:
        school = db.query(School).first()
    if not school and user_in.school_name:
        school = School(name=user_in.school_name, domain=domain, slug=domain)
        db.add(school)
        db.flush()
    elif not school:
        school = db.query(School).first()
        if not school:
            raise HTTPException(status_code=400, detail="No school found. Please provide school_name.")
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

    # Grant trial credits
    from app.services.wallet import add_credits
    from app.models import WalletPool
    from datetime import timedelta
    add_credits(
        db, new_user.id, WalletPool.TRIAL, 100,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    access_token = create_access_token({"sub": str(new_user.id), "school_id": school.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register-trial-teacher", response_model=Token)
def register_trial_teacher(user_in: UserCreate, db: Session = Depends(get_db)):
    """Instant trial: creates a teacher account linked to the demo school.

    Body accepts email, password, full_name only.
    role, subscription_plan, is_demo_account, school_id are all forced server-side.
    """
    from app.models import User, School

    # Duplicate check
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Password validation
    ok, err = validate_password_strength(user_in.password)
    if not ok:
        raise HTTPException(status_code=422, detail=err)

    # Find the unique demo school
    demo_school = db.query(School).filter(School.school_type == SchoolType.DEMO).first()
    if not demo_school:
        raise HTTPException(status_code=500, detail="Demo school not configured. Please contact support.")

    # Create user — all sensitive fields forced server-side, never from client input
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

    # Grant trial credits
    from app.services.wallet import add_credits
    from app.models import WalletPool
    from datetime import timedelta
    add_credits(
        db, new_user.id, WalletPool.TRIAL, 100,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    log_security_event("trial_teacher_registered", {
        "user_id": new_user.id,
        "email": new_user.email,
        "school_id": demo_school.id,
    })

    access_token = create_access_token({"sub": str(new_user.id), "school_id": demo_school.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/teacher-register")
def teacher_register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Public teacher registration — creates a pending TeacherRegistration request.
    No user account is created yet; admin must approve first.
    """
    from app.models import User, School, TeacherRegistration, TeacherRegistrationStatus

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    ok, err = validate_password_strength(user_in.password)
    if not ok:
        raise HTTPException(status_code=422, detail=err)

    domain = user_in.school_domain or (user_in.school_name.lower().replace(" ", "-") if user_in.school_name else None)
    school = None
    if domain:
        school = db.query(School).filter(School.domain == domain).first()
    if not school and user_in.school_name:
        school = School(name=user_in.school_name, domain=domain, slug=domain)
        db.add(school)
        db.flush()
    if not school:
        school = db.query(School).first()
        if not school:
            raise HTTPException(status_code=400, detail="No school found. Provide school_name.")

    reg = TeacherRegistration(
        school_id=school.id,
        email=user_in.email,
        full_name=user_in.full_name,
        status=TeacherRegistrationStatus.PENDING,
    )
    db.add(reg)
    db.commit()

    return {"message": "Registration request submitted. You will receive an email once reviewed.", "school_name": school.name}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    from app.models import User
    from datetime import datetime
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"LOGIN ATTEMPT: email={form_data.username}")
    user = db.query(User).filter(User.email == form_data.username).first()
    logger.info(f"USER FOUND: user_id={user.id if user else 'None'}")
    if not user or not verify_password(form_data.password, user.hashed_password):
        log_security_event("failed_login", {"email": form_data.username}, severity="WARNING")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    access_token = create_access_token({"sub": str(user.id), "school_id": user.school_id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    # FastAPI will return 200 with current user; pydantic model will serialize via orm_mode
    return current_user
