"""Database package for EDUAI Learning"""
from app.db.session import get_db, Base, engine, SessionLocal
from app.db.session import current_tenant_id

# PostgreSQL not available → skip old models to avoid conflicts
LMSClass = None
Enrollment = None
Quiz = None
QuizQuestion = None
QuizOption = None
Attempt = None
Plan = None
Subscription = None
AIUsageLog = None
Progress = None
Tenant = None

HAS_PSYCOPG2 = False

# ============ RE-EXPORT FROM NEW MODELS ============
from app.models import (
    School as Tenant,
    User,
    Course,
    Module,
    Lesson,
    Assignment,
    Submission,
    Transaction,
    TokenPackage,
    CourseEnrollment,
    ClassRoom,
    ClassroomEnrollment,
    CoursePurchase,
    Document,
    Message,
    PlatformSetting,
    TeacherRegistration,
    # Enums
    UserRole,
    SubscriptionTier,
    EnrollmentStatus,
    TransactionType,
    Currency,
    ContentType,
    CourseStatus,
    DocumentStatus,
    TeacherRegistrationStatus,
    MessageType,
    CourseState,
    EnrollStatus,
    Progress,
    # LMS Models
    Quiz,
    QuizQuestion,
    QuizOption,
    QuizAttempt,
    QuizAnswer,
    Note,
    Bookmark,
    LessonProgress,
    Certificate,
)

# Aliases for backward compatibility
Role = UserRole
PlatformSettings = PlatformSetting
Attempt = QuizAttempt

__all__ = [
    "engine",
    "SessionLocal", 
    "Base",
    "get_db",
    "HAS_PSYCOPG2",
    "current_tenant_id",
]