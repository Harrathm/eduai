"""
EDUAI Learning - Complete Database Schema
SQLAlchemy 2.0 with Multi-Tenancy Support
"""

from __future__ import annotations
from datetime import datetime, timezone, date
from enum import Enum
from typing import Optional, List
import uuid
import secrets


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float, Numeric,
    Date, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index, 
    CheckConstraint, JSON
)
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship, DeclarativeBase, 
    backref
)
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# ============================================================
# ENUMS
# ============================================================

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN_SCHOOL = "admin_school"
    SUPER_ADMIN = "super_admin"
    PEDAGOGICAL_ADMIN = "pedagogical_admin"    # super_admin_pédagogique — portée plateforme
    PEDAGOGICAL_LEAD = "pedagogical_lead"      # admin_pédagogique — portée école (school_id obligatoire)
    PARENT = "parent"                           # Parent d'élève — accès lecture seule progression

class SubscriptionTier(str, Enum):
    FREE = "free"
    TEACHER_PRO = "teacher_pro"
    SCHOOL = "school"
    INSTITUTION = "institution"


class SubscriptionPlan(str, Enum):
    """Teacher subscription plan — independent from RBAC role."""
    TRIAL = "trial"
    SCHOOL_AFFILIATED = "school_affiliated"
    INDEPENDENT_PAID = "independent_paid"


class VerificationStatus(str, Enum):
    """Light identity verification for independent teachers (non-blocking)."""
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class PaymentStatus(str, Enum):
    """Payment lifecycle status."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"


class WalletPool(str, Enum):
    """Credit pool origin — determines expiration and consumption priority."""
    TRIAL = "trial"                    # Free trial credits (expire after N days)
    SCHOOL_ALLOCATED = "school_allocated"  # Credits allocated by school admin
    PURCHASED = "purchased"            # Direct purchase (never expires)
    SUBSCRIPTION = "subscription"      # Credits included in subscription
    DT_PURCHASED = "dt_purchased"      # Real-money (TND) credits — purchase ledger


class BillableFeature(str, Enum):
    """AI features that consume credits."""
    AI_ASK = "ai_ask"                  # AI Tutor Q&A
    AI_EXPLAIN = "ai_explain"          # Concept explanation
    AI_QUIZ = "ai_quiz"                # Quiz generation
    AI_GENERATE = "ai_generate"        # Exercise/content generation
    AI_INGEST = "ai_ingest"            # PDF/text ingestion into RAG
    AI_CORRECT = "ai_correct"          # Auto-correction


class SchoolType(str, Enum):
    """Distinguishes real client schools, demo school, and individual virtual schools."""
    REAL = "real"
    DEMO = "demo"
    INDIVIDUAL = "individual"

# User limits per subscription tier
SUBSCRIPTION_LIMITS = {
    "free": 10,           # 10 users max
    "teacher_pro": 50,     # 50 users max
    "school": 200,        # 200 users max
    "institution": 1000,   # 1000 users max
}

class EnrollmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    SUSPENDED = "suspended"

class TransactionType(str, Enum):
    TOKEN_RECHARGE = "token_recharge"
    TOKEN_CONSUMPTION = "token_consumption"
    DT_DEPOSIT = "dt_deposit"
    DT_WITHDRAWAL = "dt_withdrawal"
    COURSE_PURCHASE = "course_purchase"
    COURSE_SALE = "course_sale"
    SUBSCRIPTION = "subscription"
    REFUND = "refund"
    BONUS = "bonus"
    PENALTY = "penalty"

class Currency(str, Enum):
    TOKEN = "TOKEN"
    DT = "DT"

class ContentType(str, Enum):
    VIDEO = "video"
    PDF = "pdf"
    TEXT = "text"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"

class CourseStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class PedagogicalStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED_LOCAL = "approved_local"           # validé par pedagogical_lead pour sa propre école
    APPROVED_FOR_B2B = "approved_for_b2b"       # validé par pedagogical_admin pour diffusion inter-écoles
    NEEDS_REVISION = "needs_revision"


class NiveauScolaire(str, Enum):
    """Niveaux scolaires tunisiens — primaire, préparatoire, secondaire."""
    # Primaire
    PREMIERE_ANNEE = "1ère année"
    DEUXIEME_ANNEE = "2ème année"
    TROISIEME_ANNEE = "3ème année"
    QUATRIEME_ANNEE = "4ème année"
    CINQUIEME_ANNEE = "5ème année"
    SIXIEME_ANNEE = "6ème année"
    # Préparatoire
    SEPTIEME_BASE = "7ème de base"
    HUITIEME_BASE = "8ème de base"
    NEUVIEME_BASE = "9ème de base"
    # Secondaire — 1ère année
    PREMIERE_ANNEE_SECONDAIRE = "1ère année secondaire"
    # Secondaire — 2ème année
    DEUXIEME_SCIANCES = "2ème année sciences"
    DEUXIEME_LETTRES = "2ème année lettres"
    DEUXIEME_TECH_INFO = "2ème année technologie de l'informatique"
    DEUXIEME_ECO_SERVICES = "2ème année économie et services"
    # Secondaire — 3ème année
    TROISIEME_LETTRES = "3ème année lettres"
    TROISIEME_MATHS = "3ème année mathématiques"
    TROISIEME_SC_EXP = "3ème année sciences expérimentales"
    TROISIEME_ECO_GEST = "3ème année économie et gestion"
    TROISIEME_SC_INFO = "3ème année sciences de l'informatique"
    TROISIEME_SC_TECH = "3ème année sciences techniques"
    # Secondaire — 4ème année (Baccalauréat)
    QUATRIEME_LETTRES = "4ème année lettres"
    QUATRIEME_MATHS = "4ème année mathématiques"
    QUATRIEME_SC_EXP = "4ème année sciences expérimentales"
    QUATRIEME_ECO_GEST = "4ème année économie et gestion"
    QUATRIEME_SC_INFO = "4ème année sciences de l'informatique"
    QUATRIEME_SC_TECH = "4ème année sciences techniques"


class CourseOwnerType(str, Enum):
    SCHOOL = "school"                           # propriété d'une école
    INDEPENDENT_TEACHER = "independent_teacher" # enseignant indépendant
    EDUAI_CATALOG = "eduai_catalog"             # catalogue officiel EDUAI

class CourseVisibility(str, Enum):
    PRIVATE = "private"                         # invisible, brouillon
    SCHOOL_ONLY = "school_only"                 # visible uniquement dans l'école propriétaire
    PUBLIC_CATALOG = "public_catalog"           # visible dans le catalogue public EDUAI

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TeacherRegistrationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class MessageType(str, Enum):
    BROADCAST = "broadcast"
    DIRECT = "direct"
    OBSERVATION = "observation"


# ============================================================
# CORE & MULTI-TENANCY
# ============================================================

class School(Base):
    """Multi-tenant school/organization"""
    __tablename__ = "schools"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=lambda: uuid.uuid4(), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255))

    # School type (real client, demo, or individual virtual)
    school_type: Mapped[str] = mapped_column(SQLEnum(SchoolType), default=SchoolType.REAL)
    
    # Subscription
    subscription_tier: Mapped[str] = mapped_column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    max_users: Mapped[int] = mapped_column(Integer, default=10)  # Override subscription limit
    
    # Branding
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    primary_color: Mapped[Optional[str]] = mapped_column(String(20), default="#FF6B35")
    
    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    pending_validation: Mapped[bool] = mapped_column(Boolean, default=False)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_teacher_registration: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_new_signups: Mapped[bool] = mapped_column(Boolean, default=True)
    invite_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    users: Mapped[List[User]] = relationship("User", back_populates="school", cascade="all, delete-orphan")
    courses: Mapped[List[Course]] = relationship("Course", back_populates="school", cascade="all, delete-orphan")
    transactions: Mapped[List[Transaction]] = relationship("Transaction", back_populates="school", cascade="all, delete-orphan")
    documents: Mapped[List[Document]] = relationship("Document", back_populates="school", cascade="all, delete-orphan")
    messages: Mapped[List[Message]] = relationship("Message", back_populates="school", cascade="all, delete-orphan")
    classrooms: Mapped[List["ClassRoom"]] = relationship("ClassRoom", back_populates="school", cascade="all, delete-orphan")
    course_accesses: Mapped[List["SchoolCourseAccess"]] = relationship("SchoolCourseAccess", back_populates="school", cascade="all, delete-orphan", foreign_keys="SchoolCourseAccess.school_id")
    teacher_classes: Mapped[List["TeacherClass"]] = relationship("TeacherClass", back_populates="school", cascade="all, delete-orphan", foreign_keys="TeacherClass.school_id")


class User(Base):
    """User entity with dual-economy balances"""
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("school_id", "email", name="uq_user_school_email"),
        Index("ix_users_school_id", "school_id"),
        Index("ix_users_email", "email"),
        Index("ix_users_role", "role"),
        Index("ix_users_school_role", "school_id", "role"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=lambda: uuid.uuid4(), unique=True)
    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    
    # Auth
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Role
    role: Mapped[str] = mapped_column(String(30), default=UserRole.STUDENT.value)

    # Subscription plan (teacher states A/B/C)
    subscription_plan: Mapped[str] = mapped_column(String(30), default=SubscriptionPlan.TRIAL.value)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_demo_account: Mapped[bool] = mapped_column(Boolean, default=False)

    # Langue préférée (fr, en, ar)
    language: Mapped[str] = mapped_column(String(5), default="fr")
    
    # Onboarding
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Niveau scolaire (élèves uniquement)
    niveau_scolaire: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ex: "9ème de base", "2ème année sciences"

    # Identity verification (light, non-blocking)
    verification_status: Mapped[str] = mapped_column(SQLEnum(VerificationStatus), default=VerificationStatus.UNVERIFIED)
    verification_document_url: Mapped[Optional[str]] = mapped_column(String(500))
    verification_reviewed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    verification_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verification_rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Dual-Economy Balances (DEPRECATED — use wallet service functions instead)
    # These columns are kept for backward compatibility but should be treated as read-only.
    # All mutations MUST go through app.services.wallet (credit_balance/debit_balance/credit_dt/debit_dt).
    # Balance is also computed from WalletTransaction ledger via get_dt_balance()/get_total_balance().
    token_balance: Mapped[int] = mapped_column(Integer, default=0)
    dt_balance: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)

    # Stripe
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Teacher specific
    is_approved: Mapped[Optional[bool]] = mapped_column(Boolean)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    teacher_certificate_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Account lockout (brute-force protection)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    school: Mapped[School] = relationship("School", back_populates="users")
    
    authored_courses: Mapped[List[Course]] = relationship("Course", back_populates="author", foreign_keys="Course.author_id")
    
    # Transactions (both as sender and receiver)
    transactions: Mapped[List[Transaction]] = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    
    # Enrollments
    course_enrollments: Mapped[List[CourseEnrollment]] = relationship("CourseEnrollment", back_populates="student", cascade="all, delete-orphan")
    classroom_enrollments: Mapped[List[ClassroomEnrollment]] = relationship("ClassroomEnrollment", back_populates="student", cascade="all, delete-orphan")
    
    # Submissions
    submissions: Mapped[List[Submission]] = relationship("Submission", back_populates="student", cascade="all, delete-orphan")
    
    # Documents uploaded
    documents: Mapped[List[Document]] = relationship("Document", back_populates="uploader", cascade="all, delete-orphan")
    
    # Messages
    sent_messages: Mapped[List[Message]] = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id", cascade="all, delete-orphan")
    received_messages: Mapped[List[Message]] = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id", cascade="all, delete-orphan")

    # Teacher classes (v2)
    teacher_classes: Mapped[List[TeacherClass]] = relationship("TeacherClass", back_populates="teacher", foreign_keys="TeacherClass.teacher_id", cascade="all, delete-orphan")
    student_enrollments: Mapped[List[StudentEnrollment]] = relationship("StudentEnrollment", back_populates="student", foreign_keys="StudentEnrollment.student_id", cascade="all, delete-orphan")

    # Payments (Stripe)
    payments: Mapped[List[Payment]] = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

    # Wallet ledger
    wallet_transactions: Mapped[List[WalletTransaction]] = relationship("WalletTransaction", foreign_keys="WalletTransaction.user_id", cascade="all, delete-orphan")

    # Parent–student links (N:N)
    children_links: Mapped[List["ParentEnfant"]] = relationship("ParentEnfant", foreign_keys="ParentEnfant.parent_user_id", cascade="all, delete-orphan")
    parent_links: Mapped[List["ParentEnfant"]] = relationship("ParentEnfant", foreign_keys="ParentEnfant.eleve_id", cascade="all, delete-orphan")

    # AI conversation history
    ai_conversations: Mapped[List["AIConversation"]] = relationship(
        "AIConversation", back_populates="user", cascade="all, delete-orphan"
    )


# ============================================================
# FINANCIAL AUDIT
# ============================================================

class Transaction(Base):
    """Ledger for all economy movements"""
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_school_id", "school_id"),
        Index("ix_transactions_created_at", "created_at"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=lambda: uuid.uuid4(), unique=True)
    
    # Multi-tenancy
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Transaction details
    type: Mapped[str] = mapped_column(SQLEnum(TransactionType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(SQLEnum(Currency), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    reference_id: Mapped[Optional[str]] = mapped_column(String(255))  # Could be course_id, enrollment_id, etc.
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="completed")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    school: Mapped[School] = relationship("School", back_populates="transactions")
    user: Mapped[User] = relationship("User", back_populates="transactions")


class TokenPackage(Base):
    """Pre-defined token packages for purchase"""
    __tablename__ = "token_packages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    price_dt: Mapped[float] = mapped_column(Float, nullable=False)
    bonus_tokens: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ============================================================
# LMS & ACADEMY
# ============================================================

class Course(Base):
    """Course entity"""
    __tablename__ = "courses"
    __table_args__ = (
        Index("ix_courses_school_id", "school_id"),
        Index("ix_courses_author_id", "author_id"),
        Index("ix_courses_status", "status"),
        Index("ix_courses_school_status", "school_id", "status"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=lambda: uuid.uuid4(), unique=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    modified_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    cover_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Metadata
    slug: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), default="fr")
    prerequisites: Mapped[Optional[str]] = mapped_column(Text)
    learning_objectives: Mapped[Optional[str]] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(20), default="private")  # private, school_only, public_catalog
    enrollment_type: Mapped[Optional[str]] = mapped_column(String(20), default="open")  # open, manual
    
    # Ownership
    owner_type: Mapped[str] = mapped_column(String(30), default="school")  # school, independent_teacher, eduai_catalog
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # school_id ou teacher_id selon owner_type
    
    # Pricing (monnaie réelle, distinct des crédits IA)
    price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)  # null = gratuit/inclus dans contrat
    currency: Mapped[str] = mapped_column(String(10), default="TND")
    commission_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)  # % gardé par EDUAI (independent_teacher seulement)
    
    # Pricing (crédits IA, système existant)
    price_tokens: Mapped[int] = mapped_column(Integer, default=0)
    price_dt: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Metadata
    category: Mapped[Optional[str]] = mapped_column(String(100))
    level: Mapped[Optional[str]] = mapped_column(String(50))  # beginner, intermediate, advanced
    niveau_scolaire: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # niveau scolaire tunisien (9ème de base, 2ème année sciences, etc.)
    tags: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # List of tags
    
    # Status
    status: Mapped[str] = mapped_column(SQLEnum(CourseStatus), default=CourseStatus.DRAFT)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    max_students: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Pedagogical validation
    pedagogical_status: Mapped[str] = mapped_column(String(30), default="draft")  # draft, pending_review, approved_local, approved_for_b2b, needs_revision
    validated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    validated_by_role: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # pedagogical_lead ou pedagogical_admin
    
    # Statistics
    total_modules: Mapped[int] = mapped_column(Integer, default=0)
    total_lessons: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    school: Mapped[School] = relationship("School", back_populates="courses")
    author: Mapped[User] = relationship("User", back_populates="authored_courses", foreign_keys=[author_id])
    
    modules: Mapped[List[Module]] = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    enrollments: Mapped[List[CourseEnrollment]] = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    purchases: Mapped[List[CoursePurchase]] = relationship("CoursePurchase", back_populates="course", cascade="all, delete-orphan")
    school_accesses: Mapped[List["SchoolCourseAccess"]] = relationship("SchoolCourseAccess", back_populates="course", cascade="all, delete-orphan", foreign_keys="SchoolCourseAccess.course_id")


class Module(Base):
    """Course module/chapter"""
    __tablename__ = "modules"
    __table_args__ = (
        Index("ix_modules_course_id", "course_id"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    course: Mapped[Course] = relationship("Course", back_populates="modules")
    lessons: Mapped[List[Lesson]] = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")


class Lesson(Base):
    """Individual lesson content"""
    __tablename__ = "lessons"
    __table_args__ = (
        Index("ix_lessons_module_id", "module_id"),
        Index("ix_lessons_order", "module_id", "order"),
        Index("ix_lessons_quiz_id", "quiz_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    lesson_type: Mapped[Optional[str]] = mapped_column(String(50), default="text")
    content_type: Mapped[str] = mapped_column(SQLEnum(ContentType), default=ContentType.TEXT)
    content_url: Mapped[Optional[str]] = mapped_column(String(500))
    content_text: Mapped[Optional[str]] = mapped_column(Text)
    content_html: Mapped[Optional[str]] = mapped_column(Text)

    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    video_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    video_thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    document_url: Mapped[Optional[str]] = mapped_column(String(500))
    document_type: Mapped[Optional[str]] = mapped_column(String(20))
    image_urls: Mapped[Optional[str]] = mapped_column(Text)
    link_url: Mapped[Optional[str]] = mapped_column(String(500))
    link_title: Mapped[Optional[str]] = mapped_column(String(255))

    order: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)
    is_preview: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True)

    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    ai_image_prompt: Mapped[Optional[str]] = mapped_column(Text)
    ai_video_prompt: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    module: Mapped["Module"] = relationship("Module", back_populates="lessons")
    quiz: Mapped[Optional["Quiz"]] = relationship(
        "Quiz",
        primaryjoin="Quiz.id==Lesson.quiz_id",
        foreign_keys=[quiz_id],
        viewonly=True,
        uselist=False,
    )


class ClassRoom(Base):
    """Virtual classroom for a course"""
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=lambda: uuid.uuid4(), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    invite_code: Mapped[str] = mapped_column(String(20), unique=True)

    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_students: Mapped[int] = mapped_column(Integer, default=30)

    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    school: Mapped[School] = relationship("School", back_populates="classrooms")
    teacher: Mapped[User] = relationship("User", foreign_keys=[teacher_id])
    course: Mapped[Optional[Course]] = relationship("Course")
    enrollments: Mapped[List["ClassroomEnrollment"]] = relationship(
        "ClassroomEnrollment", back_populates="classroom", cascade="all, delete-orphan"
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment", back_populates="classroom", cascade="all, delete-orphan"
    )


# ============================================================
# ENROLLMENT (Junction Tables)
# ============================================================

class CourseEnrollment(Base):
    """Enrollment in a course"""
    __tablename__ = "course_enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course"),
        Index("ix_enrollments_course_id", "course_id"),
        Index("ix_enrollments_student_id", "student_id"),
        Index("ix_enrollments_status", "status"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    
    status: Mapped[str] = mapped_column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    student: Mapped[User] = relationship("User", back_populates="course_enrollments")
    course: Mapped[Course] = relationship("Course", back_populates="enrollments")


class ClassroomEnrollment(Base):
    """Enrollment in a classroom"""
    __tablename__ = "classroom_enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "classroom_id", name="uq_student_classroom"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    
    status: Mapped[str] = mapped_column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE)
    role: Mapped[str] = mapped_column(String(50), default="student")  # student, monitor
    
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    student: Mapped[User] = relationship("User", back_populates="classroom_enrollments")
    classroom: Mapped["ClassRoom"] = relationship("ClassRoom", back_populates="enrollments")


class CoursePurchase(Base):
    """Track course purchases for revenue — système financier séparé du wallet IA."""
    __tablename__ = "course_purchases"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    
    # Montants
    amount_paid: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # montant total payé par l'élève
    currency: Mapped[str] = mapped_column(String(10), default="TND")
    platform_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)   # commission EDUAI
    teacher_revenue: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0) # montant dû à l'enseignant
    commission_rate_applied: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)  # taux appliqué lors de l'achat
    
    # Transaction
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    refunded: Mapped[bool] = mapped_column(Boolean, default=False)
    refund_reason: Mapped[Optional[str]] = mapped_column(Text)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    student: Mapped[User] = relationship("User", foreign_keys=[student_id])
    course: Mapped[Course] = relationship("Course", back_populates="purchases")

    __table_args__ = (
        Index("ix_purchases_student_id", "student_id"),
        Index("ix_purchases_course_id", "course_id"),
        Index("ix_purchases_student_course", "student_id", "course_id", unique=True),
    )


class PackStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PackPurchaseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PurchaserType(str, Enum):
    STUDENT = "student"
    SCHOOL = "school"


class StudyPack(Base):
    """Pack d'étude par niveau — donne accès à tous les cours d'un niveau scolaire."""
    __tablename__ = "study_packs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # ex: "Pack 9ème de base — Toutes matières"
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Critères d'accès
    niveau_scolaire: Mapped[str] = mapped_column(String(50), nullable=False)  # doit correspondre aux valeurs NiveauScolaire
    matieres: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # null = toutes les matières, sinon liste ["Mathématiques","Sciences"]

    # Prix
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="TND")

    # Validité
    validity_duration_days: Mapped[int] = mapped_column(Integer, default=365)

    # Statut
    status: Mapped[str] = mapped_column(String(20), default=PackStatus.DRAFT.value)

    # Propriétaire
    owner_type: Mapped[str] = mapped_column(String(30), default="eduai_catalog")  # school, eduai_catalog
    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)

    # Métadonnées
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    creator: Mapped[User] = relationship("User", foreign_keys=[created_by])
    purchases: Mapped[List["PackPurchase"]] = relationship("PackPurchase", back_populates="pack")

    __table_args__ = (
        Index("ix_study_packs_niveau", "niveau_scolaire"),
        Index("ix_study_packs_status", "status"),
    )


class PackPurchase(Base):
    """Historique des achats de packs — individuel (student) ou école (school)."""
    __tablename__ = "pack_purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pack_id: Mapped[int] = mapped_column(ForeignKey("study_packs.id", ondelete="CASCADE"), nullable=False)

    # Acheteur polymorphe : student_id OU school_id selon purchaser_type
    purchaser_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "student" ou "school"
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)

    # Période de validité
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Statut
    status: Mapped[str] = mapped_column(String(20), default=PackPurchaseStatus.ACTIVE.value)

    # Paiement
    amount_paid: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="TND")
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255))  # référence vers transaction de paiement

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    # Relationships
    pack: Mapped[StudyPack] = relationship("StudyPack", back_populates="purchases")
    student: Mapped[Optional[User]] = relationship("User", foreign_keys=[student_id])
    school: Mapped[Optional[School]] = relationship("School", foreign_keys=[school_id])

    __table_args__ = (
        Index("ix_pack_purchases_pack_id", "pack_id"),
        Index("ix_pack_purchases_student_id", "student_id"),
        Index("ix_pack_purchases_school_id", "school_id"),
        Index("ix_pack_purchases_status", "status"),
        Index("ix_pack_purchases_valid_until", "valid_until"),
    )


class Progress(Base):
    """Track lesson completion"""
    __tablename__ = "progress"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started, in_progress, completed
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[Optional[float]] = mapped_column(Float)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_progress_user_lesson", "user_id", "lesson_id", unique=True),
        Index("ix_progress_user_id", "user_id"),
        Index("ix_progress_lesson_id", "lesson_id"),
    )


# ============================================================
# ASSIGNMENTS & AI INTEGRATION
# ============================================================

class Assignment(Base):
    """Classroom assignment"""
    __tablename__ = "assignments"
    __table_args__ = (
        Index("ix_assignments_classroom_id", "classroom_id"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    
    max_score: Mapped[int] = mapped_column(Integer, default=100)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    allow_late_submission: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    classroom: Mapped["ClassRoom"] = relationship("ClassRoom", back_populates="assignments")
    submissions: Mapped[List[Submission]] = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")


class Submission(Base):
    """Student submission for assignment"""
    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_assignment_id", "assignment_id"),
        Index("ix_submissions_student_id", "student_id"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    content: Mapped[Optional[str]] = mapped_column(Text)
    file_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # AI Grading
    ai_score: Mapped[Optional[int]] = mapped_column(Integer)
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    
    is_late: Mapped[bool] = mapped_column(Boolean, default=False)
    is_graded: Mapped[bool] = mapped_column(Boolean, default=False)
    
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    assignment: Mapped[Assignment] = relationship("Assignment", back_populates="submissions")
    student: Mapped[User] = relationship("User", back_populates="submissions")


class Document(Base):
    """Document for RAG/AI embeddings"""
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_school_id", "school_id"),
        Index("ix_documents_uploader_id", "uploader_id"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=lambda: uuid.uuid4(), unique=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer)
    file_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # RAG Processing
    faiss_vector_id: Mapped[Optional[str]] = mapped_column(String(255))  # Vector database ID
    status: Mapped[str] = mapped_column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    chunk_count: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    school: Mapped[School] = relationship("School", back_populates="documents")
    uploader: Mapped[User] = relationship("User", back_populates="documents")


# ============================================================
# COMMUNICATION
# ============================================================

class Message(Base):
    """Platform messaging"""
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_school_id", "school_id"),
        Index("ix_messages_sender_id", "sender_id"),
        Index("ix_messages_receiver_id", "receiver_id"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=lambda: uuid.uuid4(), unique=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    
    # Message content
    type: Mapped[str] = mapped_column(SQLEnum(MessageType), default=MessageType.DIRECT)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Targeting
    target_audience: Mapped[Optional[str]] = mapped_column(String(50))  # all, students, teachers, specific
    recipient_role: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Priority
    is_official_observation: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Read status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    # Relationships
    school: Mapped[School] = relationship("School", back_populates="messages")
    sender: Mapped[User] = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver: Mapped[Optional[User]] = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])


# ============================================================
# PLATFORM SETTINGS
# ============================================================

class PlatformSetting(Base):
    """Platform configuration key-value store"""
    __tablename__ = "platform_settings"
    __table_args__ = (
        Index("ix_settings_school_id", "school_id"),
        Index("ix_settings_key", "school_id", "key", unique=True),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, default=None)
    
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ============================================================
# TEACHER REGISTRATION
# ============================================================

class TeacherRegistration(Base):
    """Teacher registration requests"""
    __tablename__ = "teacher_registrations"
    __table_args__ = (
        Index("ix_teacher_reg_school_id", "school_id"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)

    # Links to an existing user account (e.g. trial teacher converting to real school)
    existing_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(500))
    
    status: Mapped[str] = mapped_column(SQLEnum(TeacherRegistrationStatus), default=TeacherRegistrationStatus.PENDING)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Documents
    certificate_url: Mapped[Optional[str]] = mapped_column(String(500))
    cv_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Admin review
    reviewed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ============================================================
# EXPORT ALL MODELS
# ============================================================

__all__ = [
    "Base",
    "School",
    "User",
    "Transaction",
    "TokenPackage",
    "Course",
    "Module",
    "Lesson",
    "ClassRoom",
    "CourseEnrollment",
    "ClassroomEnrollment",
    "CoursePurchase",
    "StudyPack",
    "PackPurchase",
    "Assignment",
    "Submission",
    "Document",
    "Message",
    "PlatformSetting",
    "TeacherRegistration",
    "PlacementTest",
    "PlacementTestResult",
    "LearningGoal",
    # Enums
    "UserRole",
    "SubscriptionTier",
    "EnrollmentStatus",
    "TransactionType",
    "Currency",
    "ContentType",
    "CourseStatus",
    "NiveauScolaire",
    "PackStatus",
    "PackPurchaseStatus",
    "PurchaserType",
    "DocumentStatus",
    "TeacherRegistrationStatus",
    "MessageType",
    "GoalHorizon",
    "GoalStatus",
    "GoalMetricType",
    "GoalSource",
    # Backward compatibility aliases
    "CourseState",
    "EnrollStatus",
    "Role",
    "PlatformSettings",
]

# ============================================================
# AI USAGE LOG
# ============================================================

class AIUsageLog(Base):
    """Tracks AI API usage per user for billing/monitoring."""
    __tablename__ = "ai_usage_logs"
    __table_args__ = (
        Index("ix_ai_logs_user_id", "user_id"),
        Index("ix_ai_logs_school_id", "school_id"),
        Index("ix_ai_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    school_id: Mapped[int] = mapped_column(Integer, default=0)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])


# Backward compatibility - map to old names for router imports
CourseState = CourseStatus
EnrollStatus = EnrollmentStatus
Role = UserRole
PlatformSettings = PlatformSetting

# Map old LMS models to new ones for backward compatibility
Enrollment = CourseEnrollment
Plan = TokenPackage
Tenant = School


# ============================================================
# LMS MODELS (Quiz, Note, Bookmark, Certificate, etc.)
# ============================================================

class Quiz(Base):
    """Quiz attached to a lesson. Direct school_id for tenant filter isolation."""
    __tablename__ = "quizzes"
    __table_args__ = (
        Index("ix_quizzes_lesson_id", "lesson_id"),
        Index("ix_quizzes_school_id", "school_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    lesson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    time_limit_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    passing_score_percent: Mapped[int] = mapped_column(Integer, default=70)
    max_attempts: Mapped[Optional[int]] = mapped_column(Integer)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, default=False)
    show_results: Mapped[bool] = mapped_column(Boolean, default=True)
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, default=True)
    total_points: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    lesson: Mapped[Optional[Lesson]] = relationship(
        "Lesson",
        primaryjoin="Quiz.lesson_id==Lesson.id",
        foreign_keys=[lesson_id],
        viewonly=True,
    )
    questions: Mapped[List["QuizQuestion"]] = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts: Mapped[List["QuizAttempt"]] = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuestionType(str, Enum):
    MCQ = "mcq"
    MULTI = "multi"
    TRUE_FALSE = "truefalse"
    SHORT = "short"


class QuizQuestion(Base):
    """Quiz question"""
    __tablename__ = "quiz_questions"
    __table_args__ = (
        Index("ix_quiz_questions_quiz_id", "quiz_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), default="mcq")
    points: Mapped[int] = mapped_column(Integer, default=1)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    quiz: Mapped[Quiz] = relationship("Quiz", back_populates="questions")
    options: Mapped[List["QuizOption"]] = relationship("QuizOption", back_populates="question", cascade="all, delete-orphan")


class QuizOption(Base):
    """Quiz option"""
    __tablename__ = "quiz_options"
    __table_args__ = (
        Index("ix_quiz_options_question_id", "question_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)

    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[QuizQuestion] = relationship("QuizQuestion", back_populates="options")


class QuizAttempt(Base):
    """Student quiz attempt"""
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("ix_quiz_attempts_quiz_student", "quiz_id", "student_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    score: Mapped[Optional[float]] = mapped_column(Float)
    score_percent: Mapped[Optional[float]] = mapped_column(Float)
    correct_count: Mapped[Optional[int]] = mapped_column(Integer)
    total_count: Mapped[Optional[int]] = mapped_column(Integer)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean)

    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    quiz: Mapped[Quiz] = relationship("Quiz", back_populates="attempts")
    answers: Mapped[List["QuizAnswer"]] = relationship("QuizAnswer", back_populates="attempt", cascade="all, delete-orphan")


class QuizAnswer(Base):
    """Student answer to a question"""
    __tablename__ = "quiz_answers"
    __table_args__ = (
        Index("ix_quiz_answers_attempt_id", "attempt_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, nullable=False)

    selected_option_ids: Mapped[Optional[str]] = mapped_column(Text)
    text_answer: Mapped[Optional[str]] = mapped_column(Text)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0)

    answered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    attempt: Mapped[QuizAttempt] = relationship("QuizAttempt", back_populates="answers")


class Note(Base):
    """Learner notes per lesson"""
    __tablename__ = "notes"
    __table_args__ = (
        Index("ix_notes_user_lesson", "user_id", "lesson_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Bookmark(Base):
    """Learner bookmarks"""
    __tablename__ = "bookmarks"
    __table_args__ = (
        Index("ix_bookmarks_user_lesson", "user_id", "lesson_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, nullable=False)

    position_seconds: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LessonProgress(Base):
    """Per-lesson progress"""
    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "lesson_id", name="uq_enrollment_lesson"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(Integer, nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="not_started")
    video_position_seconds: Mapped[int] = mapped_column(Integer, default=0)
    video_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    content_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_passed: Mapped[Optional[bool]] = mapped_column(Boolean)
    quiz_score: Mapped[Optional[float]] = mapped_column(Float)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)


class Certificate(Base):
    """Course completion certificate"""
    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_cert_student_course"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False)
    enrollment_id: Mapped[int] = mapped_column(Integer, nullable=False)

    certificate_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)

    issue_date: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="ready")
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    verification_code: Mapped[str] = mapped_column(String(100), unique=True)
    grade: Mapped[Optional[float]] = mapped_column(Float)
    completion_percent: Mapped[int] = mapped_column(Integer, default=0)


class AuditAction(str, Enum):
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role_change"
    USER_BALANCE_ADJUST = "user.balance_adjust"
    SCHOOL_CREATE = "school.create"
    SCHOOL_UPDATE = "school.update"
    SCHOOL_DELETE = "school.delete"
    COURSE_PUBLISH = "course.publish"
    COURSE_UNPUBLISH = "course.unpublish"
    COURSE_DELETE = "course.delete"
    TRANSACTION_CREATE = "transaction.create"
    REGISTRATION_APPROVE = "registration.approve"
    REGISTRATION_REJECT = "registration.reject"
    SETTINGS_UPDATE = "settings.update"


class AuditLog(Base):
    """Immutable audit trail for all admin actions"""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_admin_id", "admin_id"),
        Index("ix_audit_action", "action"),
        Index("ix_audit_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admin_email: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(50))
    target_id: Mapped[Optional[int]] = mapped_column(Integer)
    details: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    admin: Mapped[Optional["User"]] = relationship("User", foreign_keys=[admin_id])


# ============================================================
# MEDIA ASSETS
# ============================================================

class MediaAsset(Base):
    """Media file asset for course content"""
    __tablename__ = "media_assets"
    __table_args__ = (
        Index("ix_media_assets_owner_id", "owner_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    storage_type: Mapped[str] = mapped_column(String(20), default="local")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# ============================================================
# B2B SCHOOL COURSE ACCESS (Academy Distribution)
# ============================================================

class SchoolCourseAccess(Base):
    """Maps which Academy courses each school has purchased/been granted access to."""
    __tablename__ = "school_course_access"
    __table_args__ = (
        Index("ix_sca_school_course", "school_id", "course_id", unique=True),
        Index("ix_sca_school_id", "school_id"),
        Index("ix_sca_course_id", "course_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    granted_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    price_paid_dt: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), default=0.0)

    school: Mapped["School"] = relationship("School", foreign_keys=[school_id])
    course: Mapped["Course"] = relationship("Course", foreign_keys=[course_id])
    grantor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[granted_by])


# ============================================================
# TEACHER-CLASS ARCHITECTURE (v2: teacher-owned classes)
# ============================================================

class TeacherClass(Base):
    """A class created by a teacher (v2 architecture).
    Unlike ClassRoom which is tied to a single course, a TeacherClass
    can have multiple courses assigned via ClassCourseAccess."""
    __tablename__ = "teacher_classes"
    __table_args__ = (
        Index("ix_tc_teacher_id", "teacher_id"),
        Index("ix_tc_school_id", "school_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    code: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    teacher: Mapped[User] = relationship("User", foreign_keys=[teacher_id])
    school: Mapped[Optional[School]] = relationship("School", foreign_keys=[school_id])
    course_accesses: Mapped[List[ClassCourseAccess]] = relationship("ClassCourseAccess", back_populates="teacher_class", cascade="all, delete-orphan")
    enrollments: Mapped[List[StudentEnrollment]] = relationship("StudentEnrollment", back_populates="teacher_class", cascade="all, delete-orphan")


class ClassCourseAccess(Base):
    """Links a course to a TeacherClass (many-to-many)."""
    __tablename__ = "class_course_access"
    __table_args__ = (
        Index("ix_cca_class_course", "class_id", "course_id", unique=True),
        Index("ix_cca_class_id", "class_id"),
        Index("ix_cca_course_id", "course_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("teacher_classes.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    teacher_class: Mapped[TeacherClass] = relationship("TeacherClass", back_populates="course_accesses")
    course: Mapped[Course] = relationship("Course", foreign_keys=[course_id])


class StudentEnrollment(Base):
    """Links a student to a TeacherClass."""
    __tablename__ = "student_enrollments"
    __table_args__ = (
        Index("ix_se_student_class", "student_id", "class_id", unique=True),
        Index("ix_se_student_id", "student_id"),
        Index("ix_se_class_id", "class_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("teacher_classes.id", ondelete="CASCADE"), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    student: Mapped[User] = relationship("User", foreign_keys=[student_id])
    teacher_class: Mapped[TeacherClass] = relationship("TeacherClass", back_populates="enrollments")


# ---------------------------------------------------------------------------
# Payment (Stripe integration for independent subscriptions)
# ---------------------------------------------------------------------------

class Payment(Base):
    """Tracks subscription payments for independent teachers."""
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payment_user_id", "user_id"),
        Index("ix_payment_stripe_session_id", "stripe_session_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # in TND
    currency: Mapped[str] = mapped_column(String(3), default="TND")
    status: Mapped[PaymentStatus] = mapped_column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    stripe_session_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, unique=True)
    stripe_payment_intent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    subscription_months: Mapped[int] = mapped_column(Integer, default=1)  # 1, 3, or 12
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship("User", back_populates="payments")


# ---------------------------------------------------------------------------
# Wallet Ledger (append-only — NEVER update, only INSERT)
# ---------------------------------------------------------------------------

class WalletTransaction(Base):
    """Immutable ledger entry for wallet credits.

    Rules:
    - ONLY INSERT — no UPDATE, no DELETE (ledger integrity)
    - Positive amount = credit added, negative amount = debit consumed
    - Balance is computed at read time by summing valid transactions
    """
    __tablename__ = "wallet_transactions"
    __table_args__ = (
        Index("ix_wallet_tx_user_id", "user_id"),
        Index("ix_wallet_tx_user_pool", "user_id", "pool"),
        Index("ix_wallet_tx_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pool: Mapped[WalletPool] = mapped_column(SQLEnum(WalletPool), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # +credit, -debit
    feature: Mapped[Optional[BillableFeature]] = mapped_column(SQLEnum(BillableFeature))  # null for credit ops
    related_request_id: Mapped[Optional[str]] = mapped_column(String(200))  # trace AI call
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)  # trial/school_allocated only
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)  # input/output tokens

    user: Mapped[User] = relationship("User", foreign_keys=[user_id], overlaps="wallet_transactions")


# ---------------------------------------------------------------------------
# Parent–Student relationship (N:N)
# ---------------------------------------------------------------------------

class ParentEnfant(Base):
    """Link between a parent and one or more students.

    A parent may have multiple children; in recomposed families a student
    could have more than one legal guardian, so no unique constraint on
    (eleve_id) alone.
    """
    __tablename__ = "parent_enfants"
    __table_args__ = (
        Index("ix_parent_enfant_parent", "parent_user_id"),
        Index("ix_parent_enfant_eleve", "eleve_id"),
        UniqueConstraint("parent_user_id", "eleve_id", name="uq_parent_eleve"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    eleve_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    parent: Mapped[User] = relationship("User", foreign_keys=[parent_user_id], back_populates="children_links")
    eleve: Mapped[User] = relationship("User", foreign_keys=[eleve_id], back_populates="parent_links")


# ---------------------------------------------------------------------------
# Pedagogical validation models
# ---------------------------------------------------------------------------

class AIContentReport(Base):
    """Signalement de contenu IA incorrect par un utilisateur."""
    __tablename__ = "ai_content_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[Optional[str]] = mapped_column(String(100))  # ID du message IA signalé
    conversation_id: Mapped[Optional[int]] = mapped_column(Integer)
    reported_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey("schools.id", ondelete="SET NULL"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, reviewing, resolved, dismissed
    resolved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolution_action: Mapped[Optional[str]] = mapped_column(Text)  # action prise
    resolution_response: Mapped[Optional[str]] = mapped_column(Text)  # réponse au signaleur
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    reporter: Mapped[User] = relationship("User", foreign_keys=[reported_by])
    resolver: Mapped[Optional[User]] = relationship("User", foreign_keys=[resolved_by])


class PedagogicalEscalation(Base):
    """Escalade d'un cas pédagogique d'un pedagogical_lead au pedagogical_admin."""
    __tablename__ = "pedagogical_escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"))
    escalated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, reviewing, resolved
    resolved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    escalator: Mapped[User] = relationship("User", foreign_keys=[escalated_by])
    resolver: Mapped[Optional[User]] = relationship("User", foreign_keys=[resolved_by])


class TeacherReassignment(Base):
    """Réaffectation temporaire d'une classe à un autre enseignant."""
    __tablename__ = "teacher_reassignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    original_teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    new_teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Plan(Base):
    """Stripe subscription plan (Free, Basic, Pro, School, Institution)."""
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float, default=0)
    interval: Mapped[str] = mapped_column(String(50), default="month")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    features: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Subscription(Base):
    """Abonnement d'une école à un plan payant."""
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("token_packages.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(50), default="active")
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    school: Mapped[School] = relationship("School")


class PlacementTest(Base):
    """Test de positionnement adaptatif — questions à difficulté croissante par matière/niveau."""
    __tablename__ = "placement_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    matiere: Mapped[str] = mapped_column(String(100), nullable=False)
    niveau: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    questions: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Format questions: [{"text": "...", "options": ["A","B","C","D"], "correct": 0, "difficulty": 1}, ...]
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class PlacementTestResult(Base):
    """Résultat d'un test de positionnement — compétence évaluée."""
    __tablename__ = "placement_test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    placement_test_id: Mapped[int] = mapped_column(ForeignKey("placement_tests.id", ondelete="CASCADE"), nullable=False)
    competency_level: Mapped[str] = mapped_column(String(30), nullable=False)  # debutant, intermediaire, avance
    answers: Mapped[Optional[dict]] = mapped_column(JSON)  # détail des réponses
    score: Mapped[Optional[float]] = mapped_column(Float)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# ============================================================
# LEARNING GOALS — Suivi d'objectifs pédagogiques
# ============================================================

class GoalHorizon(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class GoalStatus(str, Enum):
    ON_TRACK = "on_track"
    BEHIND = "behind"
    COMPLETED = "completed"
    MISSED = "missed"


class GoalMetricType(str, Enum):
    LESSONS_COMPLETED = "lessons_completed"
    QUIZ_AVERAGE_SCORE = "quiz_average_score"
    STUDY_TIME_MINUTES = "study_time_minutes"
    CHAPTER_COMPLETION = "chapter_completion"
    CURRICULUM_COVERAGE_PERCENT = "curriculum_coverage_percent"


class GoalSource(str, Enum):
    AUTO_GENERATED = "auto_generated"
    TEACHER_ASSIGNED = "teacher_assigned"
    PEDAGOGICAL_LEAD_ASSIGNED = "pedagogical_lead_assigned"
    STUDENT_SELF = "student_self"


class LearningGoal(Base):
    """
    Objectif pédagogique — le statut est TOUJOURS calculé à la volée par
    goal_tracking.compute_goal_status(), jamais stocké sur ce modèle.
    """
    __tablename__ = "learning_goals"
    __table_args__ = (
        Index("ix_learning_goals_user_id", "user_id"),
        Index("ix_learning_goals_horizon", "horizon"),
        Index("ix_learning_goals_period", "period_start", "period_end"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    matiere: Mapped[Optional[str]] = mapped_column(String(100))  # null = objectif transversal (temps d'étude)
    horizon: Mapped[str] = mapped_column(String(20), nullable=False)  # GoalHorizon
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)  # GoalMetricType
    target_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default=GoalSource.AUTO_GENERATED.value)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])


# ============================================================
# ADAPTIVE PEDAGOGICAL PATHWAY
# ============================================================


class NiveauAssimilation(str, Enum):
    """Niveau d'assimilation d'un élève pour un chapitre donné."""
    REMEDIATION = "remediation"
    STANDARD = "standard"
    AVANCE = "avance"


class TypeContenu(str, Enum):
    """Type de ressource pédagogique rattaché à une notion."""
    VIDEO = "video"
    FICHE = "fiche"
    QUIZ = "quiz"
    BANQUE_EXERCICES = "banque_exercices"
    EVALUATION_IA = "evaluation_ia"


class StatutContenuPedagogique(str, Enum):
    """Statut de publication d'un contenu (aligné sur les états existants du prof)."""
    A = "a"       # Publié / actif
    B = "b"       # Brouillon
    C = "c"       # Archivé


class StatutValidationPedagogique(str, Enum):
    """Statut de validation pédagogique d'un contenu par un responsable."""
    EN_ATTENTE = "en_attente"
    VALIDE = "valide"
    REJETE = "rejete"


class SourceChangement(str, Enum):
    """Origine d'un changement de niveau d'assimilation."""
    TEST_INITIAL = "test_initial"
    AJUSTEMENT_AUTO = "ajustement_auto"
    OVERRIDE_ENSEIGNANT = "override_enseignant"


class StatutValidationProfil(str, Enum):
    """Statut de validation d'une réorientation d'assimilation."""
    AUTO_APPLIQUE = "auto_applique"
    CONFIRME_ENSEIGNANT = "confirme_enseignant"
    ANNULE_ENSEIGNANT = "annule_enseignant"


class ActionReorientation(str, Enum):
    """Action prise par l'enseignant sur une notification de réorientation."""
    AUCUNE = "aucune"
    CONFIRME = "confirme"
    ANNULE = "annule"


class NiveauEtude(Base):
    """Arborescence : niveau d'étude (ex. 9ème de base, 1ère secondaire…)."""
    __tablename__ = "niveaux_etude"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    matieres: Mapped[List["Matiere"]] = relationship("Matiere", back_populates="niveau_etude", cascade="all, delete-orphan")


class Matiere(Base):
    """Arborescence : matière rattachée à un niveau d'étude."""
    __tablename__ = "matieres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    niveau_etude_id: Mapped[int] = mapped_column(ForeignKey("niveaux_etude.id", ondelete="CASCADE"), nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    remediation_threshold: Mapped[int] = mapped_column(Integer, default=40)
    standard_threshold: Mapped[int] = mapped_column(Integer, default=75)
    avance_threshold: Mapped[int] = mapped_column(Integer, default=75)

    niveau_etude: Mapped["NiveauEtude"] = relationship("NiveauEtude", back_populates="matieres")
    chapitres: Mapped[List["ChapterPathway"]] = relationship("ChapterPathway", back_populates="matiere", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_matieres_niveau_etude", "niveau_etude_id"),
    )


class ChapterPathway(Base):
    """Arborescence : chapitre rattaché à une matière (granularité du profil d'assimilation)."""
    __tablename__ = "chapter_pathways"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    matiere_id: Mapped[int] = mapped_column(ForeignKey("matieres.id", ondelete="CASCADE"), nullable=False)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    matiere: Mapped["Matiere"] = relationship("Matiere", back_populates="chapitres")
    notions: Mapped[List["Notion"]] = relationship("Notion", back_populates="chapitre", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chapter_pathways_matiere", "matiere_id"),
    )


class Notion(Base):
    """Arborescence : notion rattachée à un chapitre."""
    __tablename__ = "notions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapitre_id: Mapped[int] = mapped_column(ForeignKey("chapter_pathways.id", ondelete="CASCADE"), nullable=False)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    chapitre: Mapped["ChapterPathway"] = relationship("ChapterPathway", back_populates="notions")
    contenus: Mapped[List["ContenuNotion"]] = relationship("ContenuNotion", back_populates="notion", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_notions_chapitre", "chapitre_id"),
    )


class ContenuNotion(Base):
    """Contenu pédagogique rattaché à une notion pour un niveau d'assimilation donné."""
    __tablename__ = "contenus_notion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notion_id: Mapped[int] = mapped_column(ForeignKey("notions.id", ondelete="CASCADE"), nullable=False)
    niveau_assimilation: Mapped[str] = mapped_column(String(20), nullable=False)  # NiveauAssimilation
    type_ressource: Mapped[str] = mapped_column(String(30), nullable=False)  # TypeContenu
    contenu: Mapped[str] = mapped_column(Text, nullable=False)  # texte ou reference_media
    enseignant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    statut_pedagogique: Mapped[str] = mapped_column(String(10), default=StatutContenuPedagogique.A.value)
    statut_validation_pedagogique: Mapped[str] = mapped_column(String(20), default=StatutValidationPedagogique.EN_ATTENTE.value)
    valide_par: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    date_validation: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    commentaire_rejet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    notion: Mapped["Notion"] = relationship("Notion", back_populates="contenus")
    enseignant: Mapped[Optional["User"]] = relationship("User", foreign_keys=[enseignant_id])
    responsable: Mapped[Optional["User"]] = relationship("User", foreign_keys=[valide_par])

    __table_args__ = (
        Index("ix_contenus_notion_notion", "notion_id"),
        Index("ix_contenus_notion_niveau", "niveau_assimilation"),
    )


class ProfilAssimilationEleve(Base):
    """Profil d'assimilation d'un élève pour un chapitre donné."""
    __tablename__ = "profils_assimilation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    eleve_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    chapitre_id: Mapped[int] = mapped_column(ForeignKey("chapter_pathways.id", ondelete="CASCADE"), nullable=False)
    niveau_assimilation_courant: Mapped[str] = mapped_column(String(20), nullable=False)  # NiveauAssimilation
    source_changement: Mapped[str] = mapped_column(String(30), nullable=False)  # SourceChangement
    score_declencheur: Mapped[Optional[float]] = mapped_column(Float)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    statut_validation: Mapped[str] = mapped_column(String(30), nullable=False, default=StatutValidationProfil.AUTO_APPLIQUE.value)

    eleve: Mapped["User"] = relationship("User", foreign_keys=[eleve_id])
    chapitre: Mapped["ChapterPathway"] = relationship("ChapterPathway", foreign_keys=[chapitre_id])

    __table_args__ = (
        Index("ix_profils_assimilation_eleve", "eleve_id"),
        Index("ix_profils_assimilation_chapitre", "chapitre_id"),
        Index("ix_profils_assimilation_eleve_chapitre", "eleve_id", "chapitre_id"),
    )


class HistoriqueScoreEleve(Base):
    """Historique des scores d'un élève par chapitre/quiz."""
    __tablename__ = "historiques_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    eleve_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    chapitre_id: Mapped[int] = mapped_column(ForeignKey("chapter_pathways.id", ondelete="CASCADE"), nullable=False)
    quiz_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quizzes.id", ondelete="SET NULL"))
    score: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    eleve: Mapped["User"] = relationship("User", foreign_keys=[eleve_id])
    chapitre: Mapped["ChapterPathway"] = relationship("ChapterPathway", foreign_keys=[chapitre_id])

    __table_args__ = (
        Index("ix_historiques_scores_eleve_chapitre", "eleve_id", "chapitre_id"),
    )


class NotificationReorientation(Base):
    """Notification envoyée à l'enseignant lors d'une réorientation automatique."""
    __tablename__ = "notifications_reorientation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profil_assimilation_id: Mapped[int] = mapped_column(ForeignKey("profils_assimilation.id", ondelete="CASCADE"), nullable=False)
    enseignant_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date_notification: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    date_limite_action: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    action_prise: Mapped[str] = mapped_column(String(20), default=ActionReorientation.AUCUNE.value)

    profil_assimilation: Mapped["ProfilAssimilationEleve"] = relationship("ProfilAssimilationEleve", foreign_keys=[profil_assimilation_id])
    enseignant: Mapped["User"] = relationship("User", foreign_keys=[enseignant_id])

    __table_args__ = (
        Index("ix_notifications_reorientation_enseignant", "enseignant_id"),
        Index("ix_notifications_reorientation_profil", "profil_assimilation_id"),
    )


# ============================================================
# RBAC PEDAGOGIQUE — Specialites & Responsables
# ============================================================

class SpecialitePedagogique(Base):
    """Regroupement de matières par spécialité pédagogique (scope par école)."""
    __tablename__ = "specialites_pedagogiques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ecole_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    cycle_scolaire: Mapped[str] = mapped_column(String(50), nullable=False)  # 1er_cycle, 2eme_cycle

    ecole: Mapped["School"] = relationship("School")
    matieres: Mapped[List["SpecialitePedagogiqueMatiere"]] = relationship("SpecialitePedagogiqueMatiere", back_populates="specialite", cascade="all, delete-orphan")
    responsables: Mapped[List["ResponsablePedagogique"]] = relationship("ResponsablePedagogique", back_populates="specialite", cascade="all, delete-orphan")


class SpecialitePedagogiqueMatiere(Base):
    """Table de liaison spécialité → matière."""
    __tablename__ = "specialite_pedagogique_matieres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    specialite_id: Mapped[int] = mapped_column(ForeignKey("specialites_pedagogiques.id", ondelete="CASCADE"), nullable=False)
    matiere_id: Mapped[int] = mapped_column(ForeignKey("matieres.id", ondelete="CASCADE"), nullable=False)

    specialite: Mapped["SpecialitePedagogique"] = relationship("SpecialitePedagogique", back_populates="matieres")
    matiere: Mapped["Matiere"] = relationship("Matiere")

    __table_args__ = (
        UniqueConstraint("specialite_id", "matiere_id", name="uq_specialite_matiere"),
    )


class ResponsablePedagogique(Base):
    """Responsable pédagogique : user lié à une spécialité avec scope niveaux_etude."""
    __tablename__ = "responsables_pedagogiques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    specialite_id: Mapped[int] = mapped_column(ForeignKey("specialites_pedagogiques.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship("User")
    specialite: Mapped["SpecialitePedagogique"] = relationship("SpecialitePedagogique", back_populates="responsables")
    niveaux_etude_scope: Mapped[List["NiveauEtude"]] = relationship("NiveauEtude", secondary="responsable_niveaux_etude")

    __table_args__ = (
        UniqueConstraint("user_id", "specialite_id", name="uq_user_specialite"),
    )


# Table de liaison ResponsablePedagogique ↔ NiveauEtude
from sqlalchemy import Table
responsable_niveaux_etude = Table(
    "responsable_niveaux_etude",
    Base.metadata,
    Column("responsable_id", Integer, ForeignKey("responsables_pedagogiques.id", ondelete="CASCADE"), primary_key=True),
    Column("niveau_etude_id", Integer, ForeignKey("niveaux_etude.id", ondelete="CASCADE"), primary_key=True),
)


# ============================================================
# GAMIFICATION
# ============================================================

class BadgeDefinition(Base):
    """Définition d'un badge (catalogue)."""
    __tablename__ = "badge_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500))
    couleur: Mapped[str] = mapped_column(String(20), default="#F97316")
    categorie: Mapped[str] = mapped_column(String(50), nullable=False)  # progression, quiz, streak, special
    critere_type: Mapped[str] = mapped_column(String(50), nullable=False)  # quiz_count, score_avg, streak_days, chapters_completed
    critere_valeur: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=10)


class StudentBadge(Base):
    """Badge obtenu par un élève."""
    __tablename__ = "student_badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    eleve_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id: Mapped[int] = mapped_column(ForeignKey("badge_definitions.id", ondelete="CASCADE"), nullable=False)
    date_obtention: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    eleve: Mapped["User"] = relationship("User", foreign_keys=[eleve_id])
    badge: Mapped["BadgeDefinition"] = relationship("BadgeDefinition")

    __table_args__ = (
        Index("ix_student_badges_eleve", "eleve_id"),
        UniqueConstraint("eleve_id", "badge_id", name="uq_student_badge"),
    )


class StudentStreak(Base):
    """Streak quotidien d'un élève (connexions, quiz, etc)."""
    __tablename__ = "student_streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    eleve_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date_jour: Mapped[date] = mapped_column(Date, nullable=False)
    streak_login: Mapped[bool] = mapped_column(Boolean, default=False)
    streak_quiz: Mapped[bool] = mapped_column(Boolean, default=False)
    streak_objectif: Mapped[bool] = mapped_column(Boolean, default=False)
    points_jour: Mapped[int] = mapped_column(Integer, default=0)

    eleve: Mapped["User"] = relationship("User", foreign_keys=[eleve_id])

    __table_args__ = (
        Index("ix_student_streaks_eleve", "eleve_id"),
        UniqueConstraint("eleve_id", "date_jour", name="uq_student_streak_day"),
    )


class StudentRanking(Base):
    """Classement d'un élève dans son palier (par matière)."""
    __tablename__ = "student_rankings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    eleve_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    matiere_id: Mapped[Optional[int]] = mapped_column(ForeignKey("matieres.id", ondelete="SET NULL"))
    palier: Mapped[str] = mapped_column(String(20), nullable=False)  # decouverte, excellence, etablissement
    points_total: Mapped[int] = mapped_column(Integer, default=0)
    rang: Mapped[Optional[int]] = mapped_column(Integer)
    date_calcul: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    eleve: Mapped["User"] = relationship("User", foreign_keys=[eleve_id])
    matiere: Mapped[Optional["Matiere"]] = relationship("Matiere", foreign_keys=[matiere_id])

    __table_args__ = (
        Index("ix_student_rankings_eleve", "eleve_id"),
        Index("ix_student_rankings_palier", "palier"),
        Index("ix_student_rankings_matiere", "matiere_id"),
    )


# Backward compatibility aliases
Quiz = Quiz
QuizQuestion = QuizQuestion
QuizOption = QuizOption
Attempt = QuizAttempt
Progress = LessonProgress
Certificate = Certificate
AIUsageLog = AIUsageLog
Subscription = Subscription

# Import AI conversation models to register them with the mapper
from app.models_ai_conversations import AIConversation, AIChatMessage


# ---------------------------------------------------------------------------
# Password Reset Token
# ---------------------------------------------------------------------------

class PasswordResetToken(Base):
    """Secure token for password reset flow. Expires after 1 hour."""
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    school_id: Mapped[Optional[int]] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_password_reset_user", "user_id"),
        Index("ix_password_reset_school_id", "school_id"),
    )


# ---------------------------------------------------------------------------
# Refresh Token (JWT rotation)
# ---------------------------------------------------------------------------

class RefreshToken(Base):
    """Opaque refresh token stored server-side for JWT rotation.

    When the access token expires, the client sends the refresh token to
    POST /auth/refresh-token.  The server validates it, issues a new
    access+refresh pair, and invalidates the old refresh token (rotation).
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
    )


# ============================================================
# MODULE A — PÉDAGOGIQUE (hiérarchie de contenu)
# ============================================================


class TypeElementPedagogique(str, Enum):
    TEXTE = "texte"
    VIDEO = "video"
    IMAGE = "image"
    QUIZ = "quiz"
    PDF = "pdf"


class StatutElementPedagogique(str, Enum):
    BROUILLON = "brouillon"
    EN_REVIEW = "en_review"
    PUBLIE = "publie"
    REJETE = "rejete"


class NiveauDifficulte(str, Enum):
    BASIQUE = "basique"
    MOYEN = "moyen"
    DIFFICILE = "difficile"


class Competence(Base):
    """Compétence pédagogique rattachée à une matière et un niveau scolaire."""
    __tablename__ = "competences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    matiere: Mapped[str] = mapped_column(String(100), nullable=False)
    niveau_scolaire: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_competences_matiere", "matiere"),
        Index("ix_competences_niveau", "niveau_scolaire"),
    )


class Parcours(Base):
    """Parcours pédagogique regroupant chapitres et leçons."""
    __tablename__ = "parcours"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    matiere: Mapped[str] = mapped_column(String(100), nullable=False)
    niveau_scolaire: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulte: Mapped[str] = mapped_column(String(20), default="moyen")
    objectifs: Mapped[Optional[dict]] = mapped_column(JSON)
    auteur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    est_publique: Mapped[bool] = mapped_column(Boolean, default=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    auteur: Mapped[Optional["User"]] = relationship("User", foreign_keys=[auteur_id])
    chapitres: Mapped[List["Chapitre"]] = relationship("Chapitre", back_populates="parcours", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_parcours_auteur", "auteur_id"),
        Index("ix_parcours_matiere", "matiere"),
        Index("ix_parcours_niveau", "niveau_scolaire"),
    )


class Chapitre(Base):
    """Chapitre dans un parcours pédagogique."""
    __tablename__ = "chapitres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parcours_id: Mapped[int] = mapped_column(ForeignKey("parcours.id", ondelete="CASCADE"), nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    objectifs: Mapped[Optional[dict]] = mapped_column(JSON)
    ordre: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    parcours: Mapped["Parcours"] = relationship("Parcours", back_populates="chapitres")
    lecons: Mapped[List["Lecon"]] = relationship("Lecon", back_populates="chapitre", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chapitres_parcours", "parcours_id"),
    )


class Lecon(Base):
    """Leçon dans un chapitre."""
    __tablename__ = "lecons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapitre_id: Mapped[int] = mapped_column(ForeignKey("chapitres.id", ondelete="CASCADE"), nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    duree_minutes: Mapped[int] = mapped_column(Integer, default=0)
    objectifs: Mapped[Optional[dict]] = mapped_column(JSON)
    ordre: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    chapitre: Mapped["Chapitre"] = relationship("Chapitre", back_populates="lecons")
    paragraphes: Mapped[List["Paragraphe"]] = relationship("Paragraphe", back_populates="lecon", cascade="all, delete-orphan")
    elements: Mapped[List["ElementPedagogique"]] = relationship("ElementPedagogique", back_populates="lecon", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_lecons_chapitre", "chapitre_id"),
    )


class Paragraphe(Base):
    """Paragraphe auto-référencé dans une leçon."""
    __tablename__ = "paragraphes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lecon_id: Mapped[int] = mapped_column(ForeignKey("lecons.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("paragraphes.id", ondelete="CASCADE"))
    contenu: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(30), default="texte")
    ordre: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    lecon: Mapped["Lecon"] = relationship("Lecon", back_populates="paragraphes")
    parent: Mapped[Optional["Paragraphe"]] = relationship("Paragraphe", remote_side="Paragraphe.id", backref="children")

    __table_args__ = (
        Index("ix_paragraphes_lecon", "lecon_id"),
        Index("ix_paragraphes_parent", "parent_id"),
    )


# Association tables for M:N relationships (defined before ElementPedagogique)

elements_tags_matieres = Table(
    "elements_tags_matieres",
    Base.metadata,
    Column("element_id", Integer, ForeignKey("elements_pedagogiques.id", ondelete="CASCADE"), primary_key=True),
    Column("matiere_id", Integer, ForeignKey("matieres.id", ondelete="CASCADE"), primary_key=True),
)

elements_competences = Table(
    "elements_competences",
    Base.metadata,
    Column("element_id", Integer, ForeignKey("elements_pedagogiques.id", ondelete="CASCADE"), primary_key=True),
    Column("competence_id", Integer, ForeignKey("competences.id", ondelete="CASCADE"), primary_key=True),
)


class ElementPedagogique(Base):
    """Élément pédagogique (texte, vidéo, image, quiz, pdf) rattaché à une leçon ou un paragraphe."""
    __tablename__ = "elements_pedagogiques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    lecon_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lecons.id", ondelete="CASCADE"))
    paragraphe_id: Mapped[Optional[int]] = mapped_column(ForeignKey("paragraphes.id", ondelete="CASCADE"))
    matiere_id: Mapped[Optional[int]] = mapped_column(ForeignKey("matieres.id", ondelete="SET NULL"))
    niveau_etude_id: Mapped[Optional[int]] = mapped_column(ForeignKey("niveaux_etude.id", ondelete="SET NULL"))
    auteur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    statut: Mapped[str] = mapped_column(String(20), default="brouillon")
    difficulte: Mapped[str] = mapped_column(String(20), default="moyen")
    metadonnees: Mapped[Optional[dict]] = mapped_column(JSON)
    est_global: Mapped[bool] = mapped_column(Boolean, default=False)
    est_libre: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    lecon: Mapped[Optional["Lecon"]] = relationship("Lecon", back_populates="elements")
    paragraphe: Mapped[Optional["Paragraphe"]] = relationship("Paragraphe", backref="elements")
    matiere: Mapped[Optional["Matiere"]] = relationship("Matiere")
    niveau_etude: Mapped[Optional["NiveauEtude"]] = relationship("NiveauEtude")
    auteur: Mapped[Optional["User"]] = relationship("User", foreign_keys=[auteur_id])
    texte: Mapped[Optional["ElementTexte"]] = relationship("ElementTexte", back_populates="element", uselist=False)
    video: Mapped[Optional["ElementVideo"]] = relationship("ElementVideo", back_populates="element", uselist=False)
    image: Mapped[Optional["ElementImage"]] = relationship("ElementImage", back_populates="element", uselist=False)
    quiz: Mapped[Optional["ElementQuiz"]] = relationship("ElementQuiz", back_populates="element", uselist=False)
    pdf: Mapped[Optional["ElementPdf"]] = relationship("ElementPdf", back_populates="element", uselist=False)
    tags_matieres: Mapped[List["Matiere"]] = relationship("Matiere", secondary="elements_tags_matieres")

    __table_args__ = (
        Index("ix_elements_type", "type"),
        Index("ix_elements_statut", "statut"),
        Index("ix_elements_auteur", "auteur_id"),
        Index("ix_elements_matiere", "matiere_id"),
        Index("ix_elements_niveau", "niveau_etude_id"),
        Index("ix_elements_lecon", "lecon_id"),
        Index("ix_elements_paragraphe", "paragraphe_id"),
        CheckConstraint(
            "(lecon_id IS NOT NULL AND paragraphe_id IS NULL) OR (lecon_id IS NULL AND paragraphe_id IS NOT NULL)",
            name="ck_element_one_parent",
        ),
    )


class ElementTexte(Base):
    """Contenu texte d'un élément pédagogique."""
    __tablename__ = "elements_texte"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    element_id: Mapped[int] = mapped_column(ForeignKey("elements_pedagogiques.id", ondelete="CASCADE"), unique=True, nullable=False)
    corps: Mapped[str] = mapped_column(Text, nullable=False)

    element: Mapped["ElementPedagogique"] = relationship("ElementPedagogique", back_populates="texte")


class ElementVideo(Base):
    """Contenu vidéo d'un élément pédagogique."""
    __tablename__ = "elements_video"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    element_id: Mapped[int] = mapped_column(ForeignKey("elements_pedagogiques.id", ondelete="CASCADE"), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    duree_secondes: Mapped[Optional[int]] = mapped_column(Integer)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))

    element: Mapped["ElementPedagogique"] = relationship("ElementPedagogique", back_populates="video")


class ElementImage(Base):
    """Contenu image d'un élément pédagogique."""
    __tablename__ = "elements_image"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    element_id: Mapped[int] = mapped_column(ForeignKey("elements_pedagogiques.id", ondelete="CASCADE"), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(255))

    element: Mapped["ElementPedagogique"] = relationship("ElementPedagogique", back_populates="image")


class ElementQuiz(Base):
    """Contenu quiz d'un élément pédagogique."""
    __tablename__ = "elements_quiz"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    element_id: Mapped[int] = mapped_column(ForeignKey("elements_pedagogiques.id", ondelete="CASCADE"), unique=True, nullable=False)
    questions_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    score_reussite: Mapped[float] = mapped_column(Float, default=0.6)

    element: Mapped["ElementPedagogique"] = relationship("ElementPedagogique", back_populates="quiz")


class ElementPdf(Base):
    """Contenu PDF d'un élément pédagogique."""
    __tablename__ = "elements_pdf"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    element_id: Mapped[int] = mapped_column(ForeignKey("elements_pedagogiques.id", ondelete="CASCADE"), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    pages: Mapped[Optional[int]] = mapped_column(Integer)
    taille_octets: Mapped[Optional[int]] = mapped_column(Integer)

    element: Mapped["ElementPedagogique"] = relationship("ElementPedagogique", back_populates="pdf")


class ContentWorkflow(Base):
    """Audit trail des changements de statut d'un élément pédagogique."""
    __tablename__ = "content_workflow"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    element_id: Mapped[int] = mapped_column(ForeignKey("elements_pedagogiques.id", ondelete="CASCADE"), nullable=False)
    ancien_statut: Mapped[str] = mapped_column(String(20), nullable=False)
    nouveau_statut: Mapped[str] = mapped_column(String(20), nullable=False)
    commentaires: Mapped[Optional[str]] = mapped_column(Text)
    auteur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    element: Mapped["ElementPedagogique"] = relationship("ElementPedagogique", backref="workflows")
    auteur: Mapped[Optional["User"]] = relationship("User", foreign_keys=[auteur_id])

    __table_args__ = (
        Index("ix_content_workflow_element", "element_id"),
    )


class ContentPromotion(Base):
    """Historique des promotions locale → globale."""
    __tablename__ = "content_promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    element_source_id: Mapped[int] = mapped_column(ForeignKey("elements_pedagogiques.id", ondelete="CASCADE"), nullable=False)
    parcours_destination_id: Mapped[Optional[int]] = mapped_column(ForeignKey("parcours.id", ondelete="SET NULL"))
    snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    effectuee_par_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    element_source: Mapped["ElementPedagogique"] = relationship("ElementPedagogique", backref="promotions")
    parcours_destination: Mapped[Optional["Parcours"]] = relationship("Parcours")
    effectuee_par: Mapped[Optional["User"]] = relationship("User", foreign_keys=[effectuee_par_id])

    __table_args__ = (
        Index("ix_content_promotions_element", "element_source_id"),
    )


# ============================================================
# MODULE B — COMMERCIAL (abonnements, famille, licences)
# ============================================================


class TierPack(str, Enum):
    GRATUIT = "gratuit"
    BASIQUE = "basique"
    SILVER = "silver"
    GOLDEN = "golden"


class StatutAbonnement(str, Enum):
    ACTIF = "actif"
    GRACE = "grace"
    EXPIRE = "expire"
    ANNULE = "annule"


class TypeCompte(str, Enum):
    INDIVIDUEL = "individuel"
    FAMILLE = "famille"
    ECOLE = "ecole"


class PackDefinition(Base):
    """Pack d'abonnement global (pas de school_id)."""
    __tablename__ = "pack_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    niveau_scolaire: Mapped[str] = mapped_column(String(50), nullable=False)
    matieres: Mapped[Optional[dict]] = mapped_column(JSON)
    prix_tnd: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    features: Mapped[Optional[dict]] = mapped_column(JSON)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    abonnements: Mapped[List["Abonnement"]] = relationship("Abonnement", back_populates="pack")
    licences: Mapped[List["LicenceEcole"]] = relationship("LicenceEcole", back_populates="pack")

    __table_args__ = (
        Index("ix_pack_definitions_tier", "tier"),
        Index("ix_pack_definitions_niveau", "niveau_scolaire"),
    )


class Abonnement(Base):
    """Abonnement d'un utilisateur à un pack."""
    __tablename__ = "abonnements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pack_id: Mapped[int] = mapped_column(ForeignKey("pack_definitions.id", ondelete="CASCADE"), nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default="actif")
    debut: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fin: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    grace_fin: Mapped[Optional[datetime]] = mapped_column(DateTime)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship("User", backref="abonnements")
    pack: Mapped["PackDefinition"] = relationship("PackDefinition", back_populates="abonnements")

    __table_args__ = (
        Index("ix_abonnements_user", "user_id"),
        Index("ix_abonnements_pack", "pack_id"),
        Index("ix_abonnements_statut", "statut"),
    )


class CompteFamille(Base):
    """Compte famille regroupant plusieurs élèves."""
    __tablename__ = "comptes_famille"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    max_enfants: Mapped[int] = mapped_column(Integer, default=5)
    rang_famille: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    parent: Mapped["User"] = relationship("User", backref="compte_famille")
    enfants: Mapped[List["FamilleEnfant"]] = relationship("FamilleEnfant", back_populates="compte_famille", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_comptes_famille_parent", "parent_id"),
    )


class FamilleEnfant(Base):
    """Lien famille-enfant avec rang figé et remise dégressive."""
    __tablename__ = "famille_enfants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    compte_famille_id: Mapped[int] = mapped_column(ForeignKey("comptes_famille.id", ondelete="CASCADE"), nullable=False)
    eleve_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    rang: Mapped[int] = mapped_column(Integer, nullable=False)
    remise_pct: Mapped[float] = mapped_column(Float, default=0.0)
    date_ajout: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    compte_famille: Mapped["CompteFamille"] = relationship("CompteFamille", back_populates="enfants")
    eleve: Mapped["User"] = relationship("User", backref="famille_links")

    __table_args__ = (
        Index("ix_famille_enfants_compte", "compte_famille_id"),
        Index("ix_famille_enfants_eleve", "eleve_id"),
    )


class LicenceEcole(Base):
    """Pool de licences d'un école pour un pack donné."""
    __tablename__ = "licences_ecole"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ecole_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    pack_id: Mapped[int] = mapped_column(ForeignKey("pack_definitions.id", ondelete="CASCADE"), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    quantite_disponible: Mapped[int] = mapped_column(Integer, nullable=False)
    date_achat: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    ecole: Mapped["School"] = relationship("School", backref="licences")
    pack: Mapped["PackDefinition"] = relationship("PackDefinition", back_populates="licences")
    assignations: Mapped[List["LicenceAssignation"]] = relationship("LicenceAssignation", back_populates="licence", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_licences_ecole_ecole", "ecole_id"),
        Index("ix_licences_ecole_pack", "pack_id"),
    )


class LicenceAssignation(Base):
    """Affectation d'une licence à un utilisateur."""
    __tablename__ = "licence_assignations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    licence_id: Mapped[int] = mapped_column(ForeignKey("licences_ecole.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    affecte_par_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    date_affectation: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    desaffecte_a: Mapped[Optional[datetime]] = mapped_column(DateTime)

    licence: Mapped["LicenceEcole"] = relationship("LicenceEcole", back_populates="assignations")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], backref="licence_assignations")
    affecte_par: Mapped[Optional["User"]] = relationship("User", foreign_keys=[affecte_par_id])

    __table_args__ = (
        Index("ix_licence_assignations_licence", "licence_id"),
        Index("ix_licence_assignations_user", "user_id"),
    )