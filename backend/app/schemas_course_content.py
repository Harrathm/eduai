"""
Course Content Schemas - Pydantic models for API
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ Course Content Schemas ============

class CourseContentBase(BaseModel):
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    price_tokens: int = 0
    price_dt: float = 0.0
    category: Optional[str] = None
    level: str = "beginner"
    tags: Optional[List[str]] = None
    max_students: Optional[int] = None


class CourseContentCreate(CourseContentBase):
    pass


class CourseContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    price_tokens: Optional[int] = None
    price_dt: Optional[float] = None
    category: Optional[str] = None
    level: Optional[str] = None
    tags: Optional[List[str]] = None
    max_students: Optional[int] = None


class ChapterCreate(BaseModel):
    title: str
    description: Optional[str] = None
    order: int = 0


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None


class ChapterResponse(ChapterCreate):
    id: int
    course_id: int
    created_at: datetime
    lessons: List["LessonResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class CourseContentResponse(CourseContentBase):
    id: int
    school_id: int
    author_id: int
    status: str
    total_chapters: int
    total_lessons: int
    total_duration_minutes: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class CourseContentWithChapters(CourseContentResponse):
    chapters: List[ChapterResponse] = []


# ============ Lesson Schemas ============

class LessonBase(BaseModel):
    title: str
    description: Optional[str] = None
    lesson_type: str = "text"
    content_text: Optional[str] = None
    content_html: Optional[str] = None
    video_url: Optional[str] = None
    video_duration_seconds: Optional[int] = None
    video_thumbnail_url: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_page_count: Optional[int] = None
    image_urls: Optional[List[str]] = None
    link_url: Optional[str] = None
    link_title: Optional[str] = None
    order: int = 0
    duration_minutes: int = 0
    is_free: bool = False
    requires_enrollment: bool = True


class LessonCreate(LessonBase):
    chapter_id: int


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    lesson_type: Optional[str] = None
    content_text: Optional[str] = None
    content_html: Optional[str] = None
    video_url: Optional[str] = None
    video_duration_seconds: Optional[int] = None
    video_thumbnail_url: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_page_count: Optional[int] = None
    order: Optional[int] = None
    duration_minutes: Optional[int] = None
    is_free: Optional[bool] = None
    requires_enrollment: Optional[bool] = None


class LessonResponse(LessonBase):
    id: int
    chapter_id: int
    ai_generated: bool
    tokens_used: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Quiz Schemas ============

class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    passing_score_percent: int = 70
    shuffle_questions: bool = False
    shuffle_options: bool = False
    show_results: bool = True
    show_correct_answers: bool = True
    allow_retakes: bool = True
    max_attempts: Optional[int] = None


class QuizCreate(QuizBase):
    lesson_id: int


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    passing_score_percent: Optional[int] = None
    shuffle_questions: Optional[bool] = None
    shuffle_options: Optional[bool] = None
    show_results: Optional[bool] = None
    show_correct_answers: Optional[bool] = None
    allow_retakes: Optional[bool] = None
    max_attempts: Optional[int] = None


class QuizResponse(QuizBase):
    id: int
    lesson_id: int
    total_points: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizOptionCreate(BaseModel):
    option_text: str
    order: int = 0


class QuizQuestionCreate(BaseModel):
    question_text: str
    question_type: str = "multiple_choice"
    points: int = 1
    explanation: Optional[str] = None
    order: int = 0
    options: List[QuizOptionCreate]
    correct_option_ids: List[int]


class QuizQuestionResponse(BaseModel):
    id: int
    question_text: str
    question_type: str
    points: int
    explanation: Optional[str]
    order: int
    options: List[dict]
    correct_answer_ids: List[int]

    model_config = ConfigDict(from_attributes=True)


class QuizWithQuestions(QuizResponse):
    questions: List[QuizQuestionResponse] = []


# ============ Progress Schemas ============

class EnrollmentCreate(BaseModel):
    course_id: int


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    status: str
    progress_percent: int
    enrolled_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class LessonProgressUpdate(BaseModel):
    status: str = "not_started"
    video_progress_seconds: Optional[int] = None
    video_completed: Optional[bool] = None
    content_completed: Optional[bool] = None
    quiz_completed: Optional[bool] = None
    quiz_passed: Optional[bool] = None
    quiz_score: Optional[float] = None


class LessonProgressResponse(BaseModel):
    id: int
    enrollment_id: int
    lesson_id: int
    status: str
    video_progress_seconds: int
    video_completed: bool
    content_completed: bool
    quiz_completed: bool
    quiz_passed: Optional[bool]
    quiz_score: Optional[float]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class VideoProgressUpdate(BaseModel):
    current_position_seconds: int
    duration_seconds: int


# ============ Quiz Attempt Schemas ============

class QuizAnswerSubmit(BaseModel):
    question_id: int
    selected_option_ids: List[int]
    text_answer: Optional[str] = None


class QuizAttemptSubmit(BaseModel):
    answers: List[QuizAnswerSubmit]


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    student_id: int
    status: str
    score: Optional[float]
    score_percent: Optional[float]
    correct_count: Optional[int]
    total_count: Optional[int]
    passed: Optional[bool]
    started_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class QuizAttemptWithAnswers(QuizAttemptResponse):
    answers: List[dict] = []


# ============ Certificate Schemas ============

class CertificateResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    certificate_number: str
    student_name: str
    course_name: str
    issue_date: datetime
    expiry_date: Optional[datetime]
    status: str
    pdf_url: Optional[str]
    verification_code: str

    model_config = ConfigDict(from_attributes=True)


# Update forward refs
CourseContentResponse.model_rebuild()
ChapterResponse.model_rebuild()
CourseContentWithChapters.model_rebuild()