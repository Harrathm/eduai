from __future__ import annotations
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class PaginatedResponse(BaseModel):
    total: int
    items: list[Any]
    skip: int = 0
    limit: int = 20



class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    school_name: Optional[str] = None
    school_domain: Optional[str] = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    role: str
    token_balance: Optional[int] = 0
    dt_balance: Optional[float] = 0.0
    is_approved: Optional[bool] = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    total_dt_earned: Optional[float] = 0.0
    total_tokens_spent: Optional[int] = 0
    total_dt_spent: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    token_balance: Optional[int] = None
    dt_balance: Optional[float] = None
    is_approved: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    school_id: Optional[int] = None


class SchoolCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class SchoolRead(BaseModel):
    id: int
    name: str
    slug: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    plan: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClassCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    color: Optional[str] = None


class ClassRead(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    color: Optional[str] = None
    school_id: int
    teacher_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EnrollmentCreate(BaseModel):
    classroom_id: int
    student_id: int


class EnrollmentRead(BaseModel):
    id: int
    student_id: int
    classroom_id: int
    status: str
    enrolled_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentCreate(BaseModel):
    class_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class AssignmentRead(BaseModel):
    id: int
    class_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    school_id: int
    is_published: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionCreate(BaseModel):
    content: str


class SubmissionRead(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    content: str
    grade: Optional[float] = None
    ai_feedback: Optional[str] = None
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionResult(BaseModel):
    id: int
    assignment_id: int
    content: str
    grade: Optional[float] = None
    ai_feedback: str
    submitted_at: datetime


class CourseCreateSimple(BaseModel):
    title: str
    description: Optional[str] = None
    published: Optional[bool] = False
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CourseRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    school_id: int
    is_published: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CourseListRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_published: bool

    model_config = ConfigDict(from_attributes=True)


class ModuleCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    order: Optional[int] = 0


class ModuleRead(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    order: int

    model_config = ConfigDict(from_attributes=True)


class ModuleDetailRead(ModuleRead):
    lessons: list["LessonRead"] = []


class LessonCreate(BaseModel):
    module_id: int
    title: str
    content: Optional[str] = None
    duration_minutes: Optional[float] = None
    video_url: Optional[str] = None
    order: Optional[int] = 0


class LessonRead(BaseModel):
    id: int
    module_id: int
    title: str
    content: Optional[str] = None
    duration_minutes: Optional[float] = None
    video_url: Optional[str] = None
    order: int
    ai_image_prompt: Optional[str] = None
    ai_video_prompt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QuizCreate(BaseModel):
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None
    title: str
    questions: Optional[str] = None
    time_limit_minutes: Optional[float] = None


class QuizRead(BaseModel):
    id: int
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None
    title: str
    questions: Optional[str] = None
    time_limit_minutes: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class QuizQuestionCreate(BaseModel):
    quiz_id: int
    text: str
    type: Optional[str] = "mcq"
    points: Optional[float] = 1.0
    order: Optional[int] = 0


class QuizQuestionRead(BaseModel):
    id: int
    quiz_id: int
    text: str
    type: str
    points: float
    order: int

    model_config = ConfigDict(from_attributes=True)


class QuizOptionCreate(BaseModel):
    question_id: int
    text: str
    is_correct: bool = False
    order: Optional[int] = 0


class QuizOptionRead(BaseModel):
    id: int
    question_id: int
    text: str
    is_correct: bool
    order: int

    model_config = ConfigDict(from_attributes=True)


class AttemptCreate(BaseModel):
    quiz_id: int


class AttemptRead(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: Optional[float] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class PlanRead(BaseModel):
    id: int
    name: str
    stripe_price_id: Optional[str] = None
    price: int
    interval: str
    active: bool
    features: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionRead(BaseModel):
    id: int
    plan_id: Optional[int] = None
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    status: str
    started_at: datetime
    ends_at: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SubscriptionCreate(BaseModel):
    plan_id: int


class AIUsageLogRead(BaseModel):
    id: int
    user_id: int
    action: str
    tokens_used: int
    cost_usd: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIQuery(BaseModel):
    question: str
    mode: str = "tutor"
    conversation_id: Optional[int] = None


class AIResult(BaseModel):
    answer: str
    sources: list[str] = []
    conversation_id: Optional[int] = None


class ProgressRead(BaseModel):
    id: int
    user_id: int
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None
    completed: bool
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProgressCreate(BaseModel):
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None
    completed: bool = True


class AnalyticsOverview(BaseModel):
    total_users: int
    total_students: int
    total_teachers: int
    total_courses: int
    total_assignments: int
    total_submissions: int
    pending_submissions: int
    ai_requests: int
    ai_cost_usd: float


class UserAnalytics(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str] = None
    role: str
    ai_requests: int
    ai_cost_usd: float
    submissions_count: int
    avg_grade: Optional[float] = None


# Enhanced schemas for Admin Dashboard

class UserBalanceUpdate(BaseModel):
    tokens: Optional[int] = None
    dt_balance: Optional[float] = None


class UserApproval(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


class CourseCreate(BaseModel):
    title: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    cover_url: Optional[str] = None
    price_tokens: Optional[int] = 0
    price_dt: Optional[float] = 0.0
    max_students: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = "draft"
    # Access control
    visibility: Optional[str] = "public"
    enrollment_type: Optional[str] = "open"
    # Pedagogical
    level: Optional[str] = "beginner"
    category: Optional[str] = None
    tags: Optional[list] = None
    prerequisites: Optional[str] = None
    learning_objectives: Optional[str] = None
    language: Optional[str] = "fr"
    # SEO
    slug: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    cover_url: Optional[str] = None
    price_tokens: Optional[int] = None
    price_dt: Optional[float] = None
    max_students: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    # Access control
    visibility: Optional[str] = None
    enrollment_type: Optional[str] = None
    allowed_schools: Optional[list] = None
    allowed_teachers: Optional[list] = None
    # Pedagogical
    level: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list] = None
    prerequisites: Optional[str] = None
    learning_objectives: Optional[str] = None
    language: Optional[str] = None
    # SEO
    slug: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class CourseStatusUpdate(BaseModel):
    status: str
    rejection_reason: Optional[str] = None


class ModuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    order: Optional[int] = 0


class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None


class LessonCreate(BaseModel):
    title: str
    description: Optional[str] = None
    lesson_type: Optional[str] = "text"
    content_text: Optional[str] = None
    content_url: Optional[str] = None
    video_url: Optional[str] = None
    pdf_url: Optional[str] = None
    image_urls: Optional[list] = None
    link_url: Optional[str] = None
    link_title: Optional[str] = None
    duration_minutes: Optional[int] = 0
    is_free: Optional[bool] = False
    order: Optional[int] = 0


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    lesson_type: Optional[str] = None
    content_text: Optional[str] = None
    content_url: Optional[str] = None
    video_url: Optional[str] = None
    pdf_url: Optional[str] = None
    image_urls: Optional[list] = None
    link_url: Optional[str] = None
    link_title: Optional[str] = None
    duration_minutes: Optional[int] = None
    is_free: Optional[bool] = None
    order: Optional[int] = None


class LessonMediaCreate(BaseModel):
    type: str
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = 0


class QuizCreate(BaseModel):
    title: str
    course_id: int
    lesson_id: Optional[int] = None
    time_limit_minutes: Optional[float] = None
    questions: Optional[str] = None


class QuizQuestionCreate(BaseModel):
    text: str
    type: Optional[str] = "mcq"
    points: Optional[float] = 1.0
    order: Optional[int] = 0
    options: Optional[list] = None


class TeacherRegistrationCreate(BaseModel):
    full_name: str
    email: EmailStr
    qualifications: Optional[str] = None
    experience_years: Optional[int] = None


class TeacherRegistrationUpdate(BaseModel):
    status: str
    rejection_reason: Optional[str] = None


class TeacherRegistrationRead(BaseModel):
    id: int
    user_id: int
    email: str
    full_name: Optional[str] = None
    qualifications: Optional[str] = None
    experience_years: Optional[int] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    user_id: int
    type: str
    amount: float
    currency: Optional[str] = "DT"
    description: Optional[str] = None


class TransactionRead(BaseModel):
    id: int
    user_id: int
    type: str
    amount: float
    currency: str
    description: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenPackageCreate(BaseModel):
    name: str
    tokens: int
    price_dt: float
    bonus_tokens: Optional[int] = 0


class TokenPackageRead(BaseModel):
    id: int
    name: str
    tokens: int
    price_dt: float
    bonus_tokens: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AdminDashboardStats(BaseModel):
    total_users: int
    total_teachers: int
    total_students: int
    total_courses: int
    pending_courses: int
    published_courses: int
    pending_teacher_registrations: int
    total_transactions: float
    total_tokens_sold: int
    total_dt_revenue: float


class UserDetail(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    school_id: Optional[int] = None
    role: str
    token_balance: int
    dt_balance: float
    is_approved: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CourseWithDetails(BaseModel):
    id: int
    title: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    status: str
    price_tokens: int
    price_dt: float
    teacher_id: Optional[int] = None
    teacher_name: Optional[str] = None
    school_name: Optional[str] = None
    max_students: Optional[int] = None
    modules_count: int = 0
    lessons_count: int = 0
    total_chapters: int = 0
    total_lessons: int = 0
    students_enrolled: int = 0
    is_published: bool = False
    author_name: Optional[str] = None
    created_at: Optional[datetime] = None
    chapters: list = []

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    type: str = "broadcast"
    subject: str
    body: str
    recipient_id: Optional[int] = None
    recipient_role: Optional[str] = None


class MessageRead(BaseModel):
    id: int
    type: str
    subject: str
    body: str
    sender_id: int
    sender_name: Optional[str] = None
    recipient_id: Optional[int] = None
    recipient_name: Optional[str] = None
    recipient_role: Optional[str] = None
    target_audience: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettingsUpdate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class SettingsRead(BaseModel):
    id: int
    key: str
    value: Optional[str]
    description: Optional[str]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ─── Teacher Class Architecture (v2) ─────────────────────────────────

class TeacherClassCreate(BaseModel):
    name: str
    description: Optional[str] = None
    code: Optional[str] = None


class TeacherClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None


class TeacherClassRead(BaseModel):
    id: int
    teacher_id: int
    school_id: Optional[int] = None
    teacher_name: Optional[str] = None
    school_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    courses_count: int = 0
    students_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ClassCourseAccessRead(BaseModel):
    id: int
    class_id: int
    course_id: int
    course_title: Optional[str] = None
    assigned_at: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class StudentEnrollmentRead(BaseModel):
    id: int
    student_id: int
    class_id: int
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    enrolled_at: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
