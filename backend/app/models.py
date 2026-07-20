"""
EDUAI Learning - Complete Database Schema
SQLAlchemy 2.0 with Multi-Tenancy Support
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
import uuid
import secrets
from datetime import datetime, timezone
from enum import Enum


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float, 
    ForeignKey, Enum as SQLEnum, UniqueConstraint, Index, 
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
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_teacher_registration: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_new_signups: Mapped[bool] = mapped_column(Boolean, default=True)
    
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

    # Niveau scolaire (élèves uniquement)
    niveau_scolaire: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ex: "9ème de base", "2ème année sciences"

    # Identity verification (light, non-blocking)
    verification_status: Mapped[str] = mapped_column(SQLEnum(VerificationStatus), default=VerificationStatus.UNVERIFIED)
    verification_document_url: Mapped[Optional[str]] = mapped_column(String(500))
    verification_reviewed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    verification_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verification_rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Dual-Economy Balances
    token_balance: Mapped[int] = mapped_column(Integer, default=0)
    dt_balance: Mapped[float] = mapped_column(Float, default=0.0)

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
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # null = gratuit/inclus dans contrat
    currency: Mapped[str] = mapped_column(String(10), default="TND")
    commission_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # % gardé par EDUAI (independent_teacher seulement)
    
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
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False)  # montant total payé par l'élève
    currency: Mapped[str] = mapped_column(String(10), default="TND")
    platform_fee: Mapped[float] = mapped_column(Float, default=0.0)   # commission EDUAI
    teacher_revenue: Mapped[float] = mapped_column(Float, default=0.0) # montant dû à l'enseignant
    commission_rate_applied: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # taux appliqué lors de l'achat
    
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
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="TND")

    # Validité
    validity_duration_days: Mapped[int] = mapped_column(Integer, default=365)

    # Statut
    status: Mapped[str] = mapped_column(String(20), default=PackStatus.DRAFT.value)

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
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False)
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
    """Quiz attached to a lesson"""
    __tablename__ = "quizzes"
    __table_args__ = (
        Index("ix_quizzes_lesson_id", "lesson_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
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
    price_paid_dt: Mapped[Optional[float]] = mapped_column(Float, default=0.0)

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
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # in TND
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
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # +credit, -debit
    feature: Mapped[Optional[BillableFeature]] = mapped_column(SQLEnum(BillableFeature))  # null for credit ops
    related_request_id: Mapped[Optional[str]] = mapped_column(String(200))  # trace AI call
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)  # trial/school_allocated only
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)  # input/output tokens

    user: Mapped[User] = relationship("User", foreign_keys=[user_id], overlaps="wallet_transactions")


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