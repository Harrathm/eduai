"""Database session configuration"""
import os
from app.core.config import get_settings

settings = get_settings()

# Use DATABASE_URL from settings
db_url = settings.database_url if settings.database_url else "sqlite:///./eduai.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use Base from models.py so all models share the same metadata
from app.models import Base

engine = create_engine(db_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import all models to register them with Base.metadata
from app.models import (
    School, User, Course, Module, Lesson, Assignment, Submission,
    Transaction, TokenPackage, CourseEnrollment, ClassroomEnrollment,
    CoursePurchase, StudyPack, PackPurchase, Document, Message, PlatformSetting, TeacherRegistration,
    UserRole, SubscriptionTier, EnrollmentStatus, TransactionType, Currency,
    ContentType, CourseStatus, NiveauScolaire, PackStatus, PackPurchaseStatus, PurchaserType,
    DocumentStatus, TeacherRegistrationStatus, MessageType,
    Progress
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_tenant_id():
    """Get current tenant ID from context - override in routes"""
    return None


__all__ = ["engine", "SessionLocal", "Base", "get_db", "current_tenant_id"]