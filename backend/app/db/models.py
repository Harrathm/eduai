import enum
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from .base import Base
from sqlalchemy.sql import func


# Values and types for multi-tenant LMS/Academy
class UserRole(enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class EnrollmentStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"


class QuizQuestionType(enum.Enum):
    MCQ = "mcq"
    OPEN = "open"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    domain = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="tenant", cascade="all, delete-orphan")
    lms_classes = relationship("LMSClass", back_populates="tenant", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Tenant(id={self.id}, slug={self.slug})"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole, name="user_role"), nullable=False, server_default=UserRole.STUDENT.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))

    tenant = relationship("Tenant", back_populates="users")
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    teacher_of = relationship("LMSClass", back_populates="teacher", uselist=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        Index("ix_users_tenant_id", "tenant_id"),
    )

    def __repr__(self):
        return f"User(id={self.id}, email={self.email})"


class LMSClass(Base):
    __tablename__ = "lms_classes"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text)
    color = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    tenant = relationship("Tenant", back_populates="lms_classes")
    teacher = relationship("User", back_populates="teacher_of")
    enrollments = relationship("Enrollment", back_populates="lms_class", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="lms_class", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_class_tenant_code"),
        Index("ix_lms_classes_tenant_id", "tenant_id"),
    )

    def __repr__(self):
        return f"LMSClass(id={self.id}, code={self.code})"


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(Integer, ForeignKey("lms_classes.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(EnrollmentStatus, name="enrollment_status"), nullable=False, server_default=EnrollmentStatus.ACTIVE.value)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="enrollments")
    lms_class = relationship("LMSClass", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "class_id", name="uq_enrollment"),
        Index("ix_enrollments_tenant_user_class", "tenant_id", "user_id", "class_id"),
    )

    def __repr__(self):
        return f"Enrollment(id={self.id}, user_id={self.user_id}, class_id={self.class_id})"


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(Integer, ForeignKey("lms_classes.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_published = Column(Boolean, default=True)

    lms_class = relationship("LMSClass", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_assignments_tenant_class", "tenant_id", "class_id"),
    )

    def __repr__(self):
        return f"Assignment(id={self.id}, title={self.title})"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text)
    grade = Column(Float)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="submitted")

    assignment = relationship("Assignment", back_populates="submissions")
    user = relationship("User", back_populates="submissions")

    __table_args__ = (
        UniqueConstraint("assignment_id", "user_id", name="uq_submission_assignment_user"),
        Index("ix_submissions_assignment_user", "assignment_id", "user_id"),
    )

    def __repr__(self):
        return f"Submission(id={self.id}, assignment_id={self.assignment_id}, user_id={self.user_id})"


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    published = Column(Boolean, default=False)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="courses")
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_courses_tenant_id", "tenant_id"),
    )

    def __repr__(self):
        return f"Course(id={self.id}, title={self.title})"


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Module(id={self.id}, title={self.title})"


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    duration_minutes = Column(Float)
    order = Column(Integer, nullable=False, default=0)

    module = relationship("Module", back_populates="lessons")

    def __repr__(self):
        return f"Lesson(id={self.id}, title={self.title})"


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    time_limit_minutes = Column(Float)
    questions_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    course = relationship("Course", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Quiz(id={self.id}, title={self.title})"


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    type = Column(Enum(QuizQuestionType, name="quiz_question_type"), nullable=False, default=QuizQuestionType.MCQ)
    points = Column(Float, default=1.0)
    order = Column(Integer, nullable=False, default=0)

    quiz = relationship("Quiz", back_populates="questions")
    options = relationship("QuizOption", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"QuizQuestion(id={self.id}, text={self.text[:20]}...)"


class QuizOption(Base):
    __tablename__ = "quiz_options"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    order = Column(Integer, nullable=False, default=0)

    question = relationship("QuizQuestion", back_populates="options")

    def __repr__(self):
        return f"QuizOption(id={self.id}, text={self.text[:20]}...)"


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="in_progress")

    quiz = relationship("Quiz")
    user = relationship("User")

    def __repr__(self):
        return f"Attempt(id={self.id}, quiz_id={self.quiz_id}, user_id={self.user_id})"


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    stripe_plan_id = Column(String(100))
    price = Column(Float, nullable=False)
    interval = Column(String(20))  # e.g., month, year
    active = Column(Boolean, default=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="active")
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    extra_data = Column(JSON)

    tenant = relationship("Tenant", back_populates="subscriptions")
    plan = relationship("Plan")

    def __repr__(self):
        return f"Subscription(id={self.id}, tenant_id={self.tenant_id}, plan_id={self.plan_id})"
