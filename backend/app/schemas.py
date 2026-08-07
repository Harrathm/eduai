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
    school_id: Optional[int] = None
    niveau_scolaire: Optional[str] = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    role: str
    niveau_scolaire: Optional[str] = None
    subscription_plan: Optional[str] = None
    language: Optional[str] = "fr"
    onboarding_complete: Optional[bool] = False
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
    niveau_scolaire: Optional[str] = None
    language: Optional[str] = None
    token_balance: Optional[int] = None
    dt_balance: Optional[float] = None
    is_approved: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
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
    pending_validation: Optional[bool] = False
    plan: Optional[str] = None
    invite_code: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RegisterSchoolRequest(BaseModel):
    """Schema for public school registration (director self-registration)."""
    school_name: str
    school_domain: Optional[str] = None
    email: EmailStr
    password: str
    full_name: Optional[str] = None


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
    # ABAC targeting
    category_cible: Optional[str] = "Scolaire"      # Scolaire, Soft_Skill, Teacher_Training
    niveau_scolaire: Optional[str] = None            # Required when category_cible=Scolaire
    tag_pack_requis: Optional[str] = "Basic"         # Basic, Silver, Golden
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
    # ABAC targeting
    category_cible: Optional[str] = None
    niveau_scolaire: Optional[str] = None
    tag_pack_requis: Optional[str] = None
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


# ============================================================
# STUDY PACKS
# ============================================================

class StudyPackCreate(BaseModel):
    name: str
    description: Optional[str] = None
    niveau_scolaire: str
    matieres: Optional[list[str]] = None  # null = toutes les matières
    price: float
    currency: str = "TND"
    validity_duration_days: int = 365


class StudyPackUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    niveau_scolaire: Optional[str] = None
    matieres: Optional[list[str]] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    validity_duration_days: Optional[int] = None


class StudyPackRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    niveau_scolaire: str
    matieres: Optional[list[str]] = None
    price: float
    currency: str
    validity_duration_days: int
    status: str
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PackPurchaseCreate(BaseModel):
    pack_id: int


class PackPurchaseRead(BaseModel):
    id: int
    pack_id: int
    purchaser_type: str
    student_id: Optional[int] = None
    school_id: Optional[int] = None
    valid_from: datetime
    valid_until: datetime
    status: str
    amount_paid: float
    currency: str
    transaction_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ADAPTIVE PEDAGOGICAL PATHWAY
# ============================================================

class NiveauEtudeRead(BaseModel):
    id: int
    nom: str
    ordre: int
    model_config = ConfigDict(from_attributes=True)


class MatiereRead(BaseModel):
    id: int
    niveau_etude_id: int
    nom: str
    type_matiere: str = "specialite"
    remediation_threshold: int = 40
    standard_threshold: int = 75
    avance_threshold: int = 75
    model_config = ConfigDict(from_attributes=True)


class ChapterPathwayRead(BaseModel):
    id: int
    matiere_id: int
    nom: str
    ordre: int
    model_config = ConfigDict(from_attributes=True)


class NotionRead(BaseModel):
    id: int
    chapitre_id: int
    nom: str
    ordre: int
    model_config = ConfigDict(from_attributes=True)


class ContenuNotionRead(BaseModel):
    id: int
    notion_id: int
    niveau_assimilation: str
    type_ressource: str
    contenu: str
    enseignant_id: Optional[int] = None
    statut_pedagogique: str
    model_config = ConfigDict(from_attributes=True)


class ContenuNotionCreate(BaseModel):
    notion_id: int
    niveau_assimilation: str
    type_ressource: str
    contenu: str
    enseignant_id: Optional[int] = None
    statut_pedagogique: str = "a"


class ProfilAssimilationEleveRead(BaseModel):
    id: int
    eleve_id: int
    chapitre_id: int
    niveau_assimilation_courant: str
    source_changement: str
    score_declencheur: Optional[float] = None
    date: datetime
    statut_validation: str
    model_config = ConfigDict(from_attributes=True)


class ProfilAssimilationEleveCreate(BaseModel):
    eleve_id: int
    chapitre_id: int
    niveau_assimilation_courant: str
    source_changement: str
    score_declencheur: Optional[float] = None
    statut_validation: str = "auto_applique"


class StatutPublicationRead(BaseModel):
    statut: str  # "publiable" | "brouillon"
    niveaux_manquants: list[str]


class NiveauEffectifRead(BaseModel):
    eleve_id: int
    chapitre_id: int
    niveau_effectif: str
    source: str  # "profil" | "defaut_matiere"


class AccesEffectifRead(BaseModel):
    eleve_id: int
    matiere_id: int
    chapitre_id: int
    acces: bool
    niveau_effectif: Optional[str] = None


class NotificationReorientationRead(BaseModel):
    id: int
    profil_assimilation_id: int
    enseignant_id: int
    date_notification: datetime
    date_limite_action: datetime
    action_prise: str
    model_config = ConfigDict(from_attributes=True)


class ValidationReorientation(BaseModel):
    action: str  # "confirme" | "annule"


class HistoriqueScoreEleveRead(BaseModel):
    id: int
    eleve_id: int
    chapitre_id: int
    quiz_id: Optional[int] = None
    score: float
    date: datetime
    model_config = ConfigDict(from_attributes=True)


class HistoriqueScoreEleveCreate(BaseModel):
    eleve_id: int
    chapitre_id: int
    quiz_id: Optional[int] = None
    score: float


class NiveauEtudeCreate(BaseModel):
    nom: str
    ordre: int = 0


class MatiereCreate(BaseModel):
    niveau_etude_id: Optional[int] = None
    nom: Optional[str] = None
    remediation_threshold: Optional[int] = None
    standard_threshold: Optional[int] = None
    avance_threshold: Optional[int] = None


class ChapterPathwayCreate(BaseModel):
    matiere_id: int
    nom: str
    ordre: int = 0


class NotionCreate(BaseModel):
    chapitre_id: int
    nom: str
    ordre: int = 0


# ============================================================
# GAMIFICATION
# ============================================================

class StudentBadgeRead(BaseModel):
    id: int
    eleve_id: int
    badge_id: int
    date_obtention: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentStreakRead(BaseModel):
    id: int
    eleve_id: int
    date_jour: date
    streak_login: bool
    streak_quiz: bool
    streak_objectif: bool
    points_jour: int
    model_config = ConfigDict(from_attributes=True)


class StudentRankingRead(BaseModel):
    id: int
    eleve_id: int
    matiere_id: Optional[int] = None
    palier: str
    points_total: int
    rang: Optional[int] = None
    date_calcul: datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MODULE A — PÉDAGOGIQUE
# ============================================================


class CompetenceCreate(BaseModel):
    nom: str
    matiere: str
    niveau_scolaire: str
    description: Optional[str] = None


class CompetenceRead(BaseModel):
    id: int
    nom: str
    matiere: str
    niveau_scolaire: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ParcoursCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    matiere: str
    niveau_scolaire: str
    difficulte: Optional[str] = "moyen"
    objectifs: Optional[dict] = None
    est_publique: Optional[bool] = True


class ParcoursRead(BaseModel):
    id: int
    titre: str
    description: Optional[str] = None
    matiere: str
    niveau_scolaire: str
    difficulte: str
    objectifs: Optional[dict] = None
    auteur_id: Optional[int] = None
    est_publique: bool
    est_actif: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ParcoursUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    matiere: Optional[str] = None
    niveau_scolaire: Optional[str] = None
    difficulte: Optional[str] = None
    objectifs: Optional[dict] = None
    est_publique: Optional[bool] = None
    est_actif: Optional[bool] = None


class ChapitreCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    objectifs: Optional[dict] = None
    ordre: Optional[int] = 0


class ChapitreRead(BaseModel):
    id: int
    parcours_id: int
    titre: str
    description: Optional[str] = None
    objectifs: Optional[dict] = None
    ordre: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ChapitreUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    objectifs: Optional[dict] = None
    ordre: Optional[int] = None


class LeconCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    duree_minutes: Optional[int] = 0
    objectifs: Optional[dict] = None
    ordre: Optional[int] = 0


class LeconRead(BaseModel):
    id: int
    chapitre_id: int
    titre: str
    description: Optional[str] = None
    duree_minutes: int
    objectifs: Optional[dict] = None
    ordre: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class LeconUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    duree_minutes: Optional[int] = None
    objectifs: Optional[dict] = None
    ordre: Optional[int] = None


class ParagrapheCreate(BaseModel):
    contenu: str
    type: Optional[str] = "texte"
    ordre: Optional[int] = 0
    parent_id: Optional[int] = None


class ParagrapheRead(BaseModel):
    id: int
    lecon_id: int
    parent_id: Optional[int] = None
    contenu: str
    type: str
    ordre: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ParagrapheUpdate(BaseModel):
    contenu: Optional[str] = None
    type: Optional[str] = None
    ordre: Optional[int] = None
    parent_id: Optional[int] = None


class ElementPedagogiqueCreate(BaseModel):
    type: str
    titre: str
    description: Optional[str] = None
    lecon_id: Optional[int] = None
    paragraphe_id: Optional[int] = None
    matiere_id: Optional[int] = None
    niveau_etude_id: Optional[int] = None
    difficulte: Optional[str] = "moyen"
    metadonnees: Optional[dict] = None
    est_global: Optional[bool] = False
    est_libre: Optional[bool] = False


class ElementPedagogiqueRead(BaseModel):
    id: int
    type: str
    titre: str
    description: Optional[str] = None
    lecon_id: Optional[int] = None
    paragraphe_id: Optional[int] = None
    matiere_id: Optional[int] = None
    niveau_etude_id: Optional[int] = None
    auteur_id: Optional[int] = None
    statut: str
    difficulte: str
    metadonnees: Optional[dict] = None
    est_global: bool
    est_libre: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ElementPedagogiqueUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    matiere_id: Optional[int] = None
    niveau_etude_id: Optional[int] = None
    difficulte: Optional[str] = None
    metadonnees: Optional[dict] = None
    est_global: Optional[bool] = None
    est_libre: Optional[bool] = None


class ElementTexteCreate(BaseModel):
    corps: str


class ElementTexteRead(BaseModel):
    id: int
    element_id: int
    corps: str
    model_config = ConfigDict(from_attributes=True)


class ElementVideoCreate(BaseModel):
    url: str
    duree_secondes: Optional[int] = None
    thumbnail_url: Optional[str] = None


class ElementVideoRead(BaseModel):
    id: int
    element_id: int
    url: str
    duree_secondes: Optional[int] = None
    thumbnail_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ElementImageCreate(BaseModel):
    url: str
    alt_text: Optional[str] = None


class ElementImageRead(BaseModel):
    id: int
    element_id: int
    url: str
    alt_text: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ElementQuizCreate(BaseModel):
    questions_json: dict
    score_reussite: Optional[float] = 0.6


class ElementQuizRead(BaseModel):
    id: int
    element_id: int
    questions_json: dict
    score_reussite: float
    model_config = ConfigDict(from_attributes=True)


class ElementPdfCreate(BaseModel):
    url: str
    pages: Optional[int] = None
    taille_octets: Optional[int] = None


class ElementPdfRead(BaseModel):
    id: int
    element_id: int
    url: str
    pages: Optional[int] = None
    taille_octets: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class ContentWorkflowRead(BaseModel):
    id: int
    element_id: int
    ancien_statut: str
    nouveau_statut: str
    commentaires: Optional[str] = None
    auteur_id: Optional[int] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ContentPromotionRead(BaseModel):
    id: int
    element_source_id: int
    parcours_destination_id: Optional[int] = None
    snapshot_json: dict
    effectuee_par_id: Optional[int] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MODULE B — COMMERCIAL
# ============================================================


class PackDefinitionCreate(BaseModel):
    nom: str
    description: Optional[str] = None
    tier: str
    niveau_scolaire: str
    matieres: Optional[dict] = None
    prix_tnd: Optional[float] = 0
    features: Optional[dict] = None
    est_actif: Optional[bool] = True


class PackDefinitionRead(BaseModel):
    id: int
    nom: str
    description: Optional[str] = None
    tier: str
    niveau_scolaire: str
    matieres: Optional[dict] = None
    prix_tnd: float
    features: Optional[dict] = None
    est_actif: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class PackDefinitionUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    tier: Optional[str] = None
    niveau_scolaire: Optional[str] = None
    matieres: Optional[dict] = None
    prix_tnd: Optional[float] = None
    features: Optional[dict] = None
    est_actif: Optional[bool] = None


class AbonnementCreate(BaseModel):
    pack_id: int


class AbonnementRead(BaseModel):
    id: int
    user_id: int
    pack_id: int
    statut: str
    debut: datetime
    fin: datetime
    grace_fin: Optional[datetime] = None
    scheduled_tier: Optional[str] = None
    scheduled_effective_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ChangeTierRequest(BaseModel):
    target_pack_id: int


class MonPackRead(BaseModel):
    current_tier: str
    current_pack: Optional[dict] = None
    abonnement: Optional[dict] = None
    available_packs: list = []
    scheduled_change: Optional[dict] = None
    niveau_scolaire: Optional[str] = None
    quota_info: dict = {}


class CompteFamilleRead(BaseModel):
    id: int
    parent_id: int
    max_enfants: int
    rang_famille: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class FamilleEnfantCreate(BaseModel):
    eleve_id: int


class FamilleEnfantRead(BaseModel):
    id: int
    compte_famille_id: int
    eleve_id: int
    rang: int
    remise_pct: float
    date_ajout: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class LicenceEcoleCreate(BaseModel):
    pack_id: int
    quantite: int


class LicenceEcoleRead(BaseModel):
    id: int
    ecole_id: int
    pack_id: int
    quantite: int
    quantite_disponible: int
    date_achat: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class LicenceAssignationCreate(BaseModel):
    user_id: int


class LicenceAssignationRead(BaseModel):
    id: int
    licence_id: int
    user_id: int
    affecte_par_id: Optional[int] = None
    date_affectation: Optional[datetime] = None
    desaffecte_a: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
