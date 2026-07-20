"""
LMS Models - Course Content, Quiz, Progress, Certificates
Uses separate LmsBase to avoid mapper conflicts with platform models.
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float, 
    ForeignKey, Enum as SQLEnum, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.orm import foreign


class LmsBase(DeclarativeBase):
    """Separate Base for course-builder models to avoid mapper conflicts."""
    pass


# Import platform models for relationships
from app.models import User


# ============ Enums ============

class CourseContentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class EnrollmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    SUSPENDED = "suspended"


class CertificateStatus(str, Enum):
    GENERATING = "generating"
    READY = "ready"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ============ Course Models ============

class CourseContent(LmsBase):
    """Course content - Super Admin authored courses"""
    __tablename__ = "cb_course_contents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school_id: Mapped[int] = mapped_column(Integer, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    price_tokens: Mapped[int] = mapped_column(Integer, default=0)
    price_dt: Mapped[float] = mapped_column(Float, default=0.0)
    
    category: Mapped[Optional[str]] = mapped_column(String(100))
    level: Mapped[str] = mapped_column(String(50), default="beginner")
    tags: Mapped[Optional[str]] = mapped_column(JSON)
    
    status: Mapped[str] = mapped_column(String(20), default="draft")
    max_students: Mapped[Optional[int]] = mapped_column(Integer)
    
    total_chapters: Mapped[int] = mapped_column(Integer, default=0)
    total_lessons: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    chapters: Mapped[List[Chapter]] = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")
    enrollments: Mapped[List[CourseEnrollment]] = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")


class Chapter(LmsBase):
    """Chapter/Section within a course"""
    __tablename__ = "cb_chapters"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("cb_course_contents.id", ondelete="CASCADE"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    course: Mapped[CourseContent] = relationship("CourseContent", back_populates="chapters")
    lessons: Mapped[List[Lesson]] = relationship("Lesson", back_populates="chapter", cascade="all, delete-orphan")


class LessonType(str, Enum):
    VIDEO = "video"
    PDF = "pdf"
    TEXT = "text"
    QUIZ = "quiz"
    IMAGE = "image"
    LINK = "link"
    VIDEO_TEXT = "video_text"
    DOCUMENT = "document"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    MULTIPLE_SELECT = "multiple_select"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_BLANK = "fill_blank"


class Lesson(LmsBase):
    """Individual lesson content"""
    __tablename__ = "cb_lessons"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("cb_chapters.id", ondelete="CASCADE"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    lesson_type: Mapped[str] = mapped_column(SQLEnum(LessonType), default=LessonType.TEXT)
    
    # Text content
    content_text: Mapped[Optional[str]] = mapped_column(Text)
    content_html: Mapped[Optional[str]] = mapped_column(Text)
    
    # Video
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    video_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    video_thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # PDF/Document
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    pdf_page_count: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Images
    image_urls: Mapped[Optional[str]] = mapped_column(JSON)  # Array of image URLs
    
    # Links
    link_url: Mapped[Optional[str]] = mapped_column(String(500))
    link_title: Mapped[Optional[str]] = mapped_column(String(255))
    
    order: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_enrollment: Mapped[bool] = mapped_column(Boolean, default=True)
    
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_prompt: Mapped[Optional[str]] = mapped_column(Text)
    ai_model: Mapped[Optional[str]] = mapped_column(String(50))
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    chapter: Mapped[Chapter] = relationship("Chapter", back_populates="lessons")
    quiz: Mapped[Optional[Quiz]] = relationship("Quiz", back_populates="lesson", uselist=False)


# ============ Quiz Models ============

class Quiz(LmsBase):
    """Quiz attached to a lesson"""
    __tablename__ = "cb_quizzes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("cb_lessons.id", ondelete="CASCADE"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    passing_score_percent: Mapped[int] = mapped_column(Integer, default=70)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, default=False)
    
    show_results: Mapped[bool] = mapped_column(Boolean, default=True)
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_retakes: Mapped[bool] = mapped_column(Boolean, default=True)
    max_attempts: Mapped[Optional[int]] = mapped_column(Integer)
    
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    
    lesson: Mapped[Lesson] = relationship("Lesson", back_populates="quiz")
    questions: Mapped[List[QuizQuestion]] = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts: Mapped[List[QuizAttempt]] = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(LmsBase):
    """Quiz question"""
    __tablename__ = "cb_quiz_questions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("cb_quizzes.id", ondelete="CASCADE"), nullable=False)
    
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(SQLEnum(QuestionType), default=QuestionType.MULTIPLE_CHOICE)
    
    points: Mapped[int] = mapped_column(Integer, default=1)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    quiz: Mapped[Quiz] = relationship("Quiz", back_populates="questions")
    options: Mapped[List[QuizOption]] = relationship("QuizOption", back_populates="question", cascade="all, delete-orphan")
    correct_answers: Mapped[List[CorrectAnswer]] = relationship("CorrectAnswer", back_populates="question", cascade="all, delete-orphan")


class QuizOption(LmsBase):
    """Quiz answer option"""
    __tablename__ = "cb_quiz_options"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("cb_quiz_questions.id", ondelete="CASCADE"), nullable=False)
    
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    question: Mapped[QuizQuestion] = relationship("QuizQuestion", back_populates="options")


class CorrectAnswer(LmsBase):
    """Correct answer(s) for a question"""
    __tablename__ = "cb_correct_answers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("cb_quiz_questions.id", ondelete="CASCADE"), nullable=False)
    
    option_id: Mapped[int] = mapped_column(ForeignKey("cb_quiz_options.id", ondelete="CASCADE"), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    question: Mapped[QuizQuestion] = relationship("QuizQuestion", back_populates="correct_answers")


class QuizAttempt(LmsBase):
    """Student quiz attempt"""
    __tablename__ = "cb_quiz_attempts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("cb_quizzes.id", ondelete="CASCADE"), nullable=False)
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
    student: Mapped[User] = relationship(User, primaryjoin=lambda: foreign(QuizAttempt.student_id) == User.id, viewonly=True)
    answers: Mapped[List[StudentAnswer]] = relationship("StudentAnswer", back_populates="attempt", cascade="all, delete-orphan")


class StudentAnswer(LmsBase):
    """Student's answer to a question"""
    __tablename__ = "cb_student_answers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("cb_quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("cb_quiz_questions.id", ondelete="CASCADE"), nullable=False)
    
    selected_option_ids: Mapped[Optional[str]] = mapped_column(JSON)
    text_answer: Mapped[Optional[str]] = mapped_column(Text)
    
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    points_earned: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    
    attempt: Mapped[QuizAttempt] = relationship("QuizAttempt", back_populates="answers")


# ============ Progress Models ============

class CourseEnrollment(LmsBase):
    """Course enrollment tracking"""
    __tablename__ = "cb_course_enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_cb_enrollment_student_course"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("cb_course_contents.id", ondelete="CASCADE"), nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="active")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    student: Mapped[User] = relationship(User, primaryjoin=lambda: foreign(CourseEnrollment.student_id) == User.id, viewonly=True)
    course: Mapped[CourseContent] = relationship("CourseContent", back_populates="enrollments")
    lesson_progress: Mapped[List[LessonProgress]] = relationship("LessonProgress", back_populates="enrollment", cascade="all, delete-orphan")


class LessonProgress(LmsBase):
    """Per-lesson progress tracking"""
    __tablename__ = "cb_lesson_progress"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "lesson_id", name="uq_cb_enrollment_lesson"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("cb_course_enrollments.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("cb_lessons.id", ondelete="CASCADE"), nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="not_started")
    
    video_progress_seconds: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    video_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    content_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_passed: Mapped[Optional[bool]] = mapped_column(Boolean)
    quiz_score: Mapped[Optional[float]] = mapped_column(Float)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    enrollment: Mapped[CourseEnrollment] = relationship("CourseEnrollment", back_populates="lesson_progress")


class VideoWatchProgress(LmsBase):
    """Detailed video watch progress"""
    __tablename__ = "cb_video_watch_progress"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "lesson_id", name="uq_cb_video_enrollment_lesson"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("cb_course_enrollments.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("cb_lessons.id", ondelete="CASCADE"), nullable=False)
    
    current_position_seconds: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    percent_watched: Mapped[float] = mapped_column(Float, default=0.0)
    
    last_watched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# ============ Certificate Models ============

class Certificate(LmsBase):
    """Course completion certificate"""
    __tablename__ = "cb_certificates"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_cb_cert_student_course"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)  # FK to users.id
    course_id: Mapped[int] = mapped_column(ForeignKey("cb_course_contents.id", ondelete="CASCADE"), nullable=False)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("cb_course_enrollments.id", ondelete="CASCADE"), nullable=False)
    
    certificate_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    issue_date: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    status: Mapped[str] = mapped_column(SQLEnum(CertificateStatus), default=CertificateStatus.READY)
    
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    verification_code: Mapped[str] = mapped_column(String(100), unique=True)
    
    grade: Mapped[Optional[float]] = mapped_column(Float)
    completion_percent: Mapped[int] = mapped_column(Integer, default=0)
    
    student: Mapped[User] = relationship(User, primaryjoin=lambda: foreign(Certificate.student_id) == User.id, viewonly=True)
    course: Mapped[CourseContent] = relationship("CourseContent")
    enrollment: Mapped[CourseEnrollment] = relationship("CourseEnrollment")
