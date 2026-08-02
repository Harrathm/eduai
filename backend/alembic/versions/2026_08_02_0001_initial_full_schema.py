"""initial schema - complete database with all tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-02 14:20:06.916607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Table: badge_definitions ---
    op.create_table(
        'badge_definitions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nom', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon_url', sa.String(500)),
        sa.Column('couleur', sa.String(20), nullable=False, default='#F97316'),
        sa.Column('categorie', sa.String(50), nullable=False),
        sa.Column('critere_type', sa.String(50), nullable=False),
        sa.Column('critere_valeur', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False, default=10),
        sa.UniqueConstraint('nom'),
    )

    # --- Table: bookmarks ---
    op.create_table(
        'bookmarks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('position_seconds', sa.Integer(), nullable=False, default=0),
        sa.Column('note', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Index('ix_bookmarks_user_lesson', 'user_id', 'lesson_id', postgresql_using='btree'),
    )

    # --- Table: cb_course_contents ---
    op.create_table(
        'cb_course_contents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('thumbnail_url', sa.String(500)),
        sa.Column('price_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('price_dt', sa.Float(), nullable=False, default=0.0),
        sa.Column('category', sa.String(100)),
        sa.Column('level', sa.String(50), nullable=False, default='beginner'),
        sa.Column('tags', sa.JSON()),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('max_students', sa.Integer()),
        sa.Column('total_chapters', sa.Integer(), nullable=False, default=0),
        sa.Column('total_lessons', sa.Integer(), nullable=False, default=0),
        sa.Column('total_duration_minutes', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime()),
    )

    # --- Table: certificates ---
    op.create_table(
        'certificates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('certificate_number', sa.String(50), nullable=False, unique=True),
        sa.Column('student_name', sa.String(255), nullable=False),
        sa.Column('course_name', sa.String(255), nullable=False),
        sa.Column('issue_date', sa.DateTime(), nullable=False),
        sa.Column('expiry_date', sa.DateTime()),
        sa.Column('status', sa.String(20), nullable=False, default='ready'),
        sa.Column('pdf_url', sa.String(500)),
        sa.Column('verification_code', sa.String(100), nullable=False, unique=True),
        sa.Column('grade', sa.Float()),
        sa.Column('completion_percent', sa.Integer(), nullable=False, default=0),
        sa.UniqueConstraint('certificate_number'),
        sa.UniqueConstraint('student_id', 'course_id', name='uq_cert_student_course'),
        sa.UniqueConstraint('verification_code'),
    )

    # --- Table: lesson_progress ---
    op.create_table(
        'lesson_progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='not_started'),
        sa.Column('video_position_seconds', sa.Integer(), nullable=False, default=0),
        sa.Column('video_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('content_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('quiz_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('quiz_passed', sa.Boolean()),
        sa.Column('quiz_score', sa.Float()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, default=0),
        sa.UniqueConstraint('enrollment_id', 'lesson_id', name='uq_enrollment_lesson'),
    )

    # --- Table: lessons ---
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('module_id', sa.Integer(), sa.ForeignKey('modules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('lesson_type', sa.String(50), default='text'),
        sa.Column('content_type', sa.String(10), nullable=False, default='text'),
        sa.Column('content_url', sa.String(500)),
        sa.Column('content_text', sa.Text()),
        sa.Column('content_html', sa.Text()),
        sa.Column('video_url', sa.String(500)),
        sa.Column('video_duration_seconds', sa.Integer()),
        sa.Column('video_thumbnail_url', sa.String(500)),
        sa.Column('pdf_url', sa.String(500)),
        sa.Column('document_url', sa.String(500)),
        sa.Column('document_type', sa.String(20)),
        sa.Column('image_urls', sa.Text()),
        sa.Column('link_url', sa.String(500)),
        sa.Column('link_title', sa.String(255)),
        sa.Column('order', sa.Integer(), nullable=False, default=0),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, default=0),
        sa.Column('is_free', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_preview', sa.Boolean(), nullable=False, default=False),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('quizzes.id', ondelete='SET NULL')),
        sa.Column('ai_generated', sa.Boolean(), nullable=False, default=False),
        sa.Column('tokens_used', sa.Integer()),
        sa.Column('ai_image_prompt', sa.Text()),
        sa.Column('ai_video_prompt', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Index('ix_lessons_module_id', 'module_id', postgresql_using='btree'),
        sa.Index('ix_lessons_quiz_id', 'quiz_id', postgresql_using='btree'),
        sa.Index('ix_lessons_order', 'module_id', 'order', postgresql_using='btree'),
    )

    # --- Table: media_assets ---
    op.create_table(
        'media_assets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False, default=0),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('storage_type', sa.String(20), nullable=False, default='local'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Index('ix_media_assets_owner_id', 'owner_id', postgresql_using='btree'),
    )

    # --- Table: niveaux_etude ---
    op.create_table(
        'niveaux_etude',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nom', sa.String(100), nullable=False, unique=True),
        sa.Column('ordre', sa.Integer(), nullable=False, default=0),
        sa.UniqueConstraint('nom'),
    )

    # --- Table: notes ---
    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_notes_user_lesson', 'user_id', 'lesson_id', postgresql_using='btree'),
    )

    # --- Table: quizzes ---
    op.create_table(
        'quizzes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('lesson_id', sa.Integer(), sa.ForeignKey('lessons.id', ondelete='SET NULL')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('time_limit_seconds', sa.Integer()),
        sa.Column('passing_score_percent', sa.Integer(), nullable=False, default=70),
        sa.Column('max_attempts', sa.Integer()),
        sa.Column('shuffle_questions', sa.Boolean(), nullable=False, default=False),
        sa.Column('shuffle_options', sa.Boolean(), nullable=False, default=False),
        sa.Column('show_results', sa.Boolean(), nullable=False, default=True),
        sa.Column('show_correct_answers', sa.Boolean(), nullable=False, default=True),
        sa.Column('total_points', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_quizzes_lesson_id', 'lesson_id', postgresql_using='btree'),
    )

    # --- Table: schools ---
    op.create_table(
        'schools',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uuid', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('domain', sa.String(255)),
        sa.Column('school_type', sa.String(10), nullable=False, default='real'),
        sa.Column('subscription_tier', sa.String(11), nullable=False, default='free'),
        sa.Column('subscription_expires_at', sa.DateTime()),
        sa.Column('max_users', sa.Integer(), nullable=False, default=10),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('primary_color', sa.String(20), default='#FF6B35'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('pending_validation', sa.Boolean(), nullable=False, default=False),
        sa.Column('maintenance_mode', sa.Boolean(), nullable=False, default=False),
        sa.Column('allow_teacher_registration', sa.Boolean(), nullable=False, default=True),
        sa.Column('allow_new_signups', sa.Boolean(), nullable=False, default=True),
        sa.Column('invite_code', sa.String(20), unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('invite_code'),
        sa.UniqueConstraint('uuid'),
    )

    # --- Table: cb_chapters ---
    op.create_table(
        'cb_chapters',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('cb_course_contents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # --- Table: cb_course_enrollments ---
    op.create_table(
        'cb_course_enrollments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('cb_course_contents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('progress_percent', sa.Integer(), nullable=False, default=0),
        sa.Column('enrolled_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.UniqueConstraint('student_id', 'course_id', name='uq_cb_enrollment_student_course'),
    )

    # --- Table: matieres ---
    op.create_table(
        'matieres',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('niveau_etude_id', sa.Integer(), sa.ForeignKey('niveaux_etude.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nom', sa.String(100), nullable=False),
        sa.Column('remediation_threshold', sa.Integer(), nullable=False, default=40),
        sa.Column('standard_threshold', sa.Integer(), nullable=False, default=75),
        sa.Column('avance_threshold', sa.Integer(), nullable=False, default=75),
        sa.Index('ix_matieres_niveau_etude', 'niveau_etude_id', postgresql_using='btree'),
    )

    # --- Table: platform_settings ---
    op.create_table(
        'platform_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE')),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text()),
        sa.Column('description', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_settings_school_id', 'school_id', postgresql_using='btree'),
        sa.Index('ix_settings_key', 'school_id', 'key', unique=True, postgresql_using='btree'),
    )

    # --- Table: quiz_attempts ---
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='in_progress'),
        sa.Column('score', sa.Float()),
        sa.Column('score_percent', sa.Float()),
        sa.Column('correct_count', sa.Integer()),
        sa.Column('total_count', sa.Integer()),
        sa.Column('passed', sa.Boolean()),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('graded_at', sa.DateTime()),
        sa.Index('ix_quiz_attempts_quiz_student', 'quiz_id', 'student_id', postgresql_using='btree'),
    )

    # --- Table: quiz_questions ---
    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(20), nullable=False, default='mcq'),
        sa.Column('points', sa.Integer(), nullable=False, default=1),
        sa.Column('explanation', sa.Text()),
        sa.Column('order_index', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Index('ix_quiz_questions_quiz_id', 'quiz_id', postgresql_using='btree'),
    )

    # --- Table: specialites_pedagogiques ---
    op.create_table(
        'specialites_pedagogiques',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ecole_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nom', sa.String(100), nullable=False),
        sa.Column('cycle_scolaire', sa.String(50), nullable=False),
    )

    # --- Table: token_packages ---
    op.create_table(
        'token_packages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('tokens', sa.Integer(), nullable=False),
        sa.Column('price_dt', sa.Float(), nullable=False),
        sa.Column('bonus_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # --- Table: users ---
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uuid', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('role', sa.String(30), nullable=False, default='student'),
        sa.Column('subscription_plan', sa.String(30), nullable=False, default='trial'),
        sa.Column('subscription_expires_at', sa.DateTime()),
        sa.Column('is_demo_account', sa.Boolean(), nullable=False, default=False),
        sa.Column('language', sa.String(5), nullable=False, default='fr'),
        sa.Column('onboarding_complete', sa.Boolean(), nullable=False, default=False),
        sa.Column('niveau_scolaire', sa.String(50)),
        sa.Column('verification_status', sa.String(10), nullable=False, default='unverified'),
        sa.Column('verification_document_url', sa.String(500)),
        sa.Column('verification_reviewed_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('verification_reviewed_at', sa.DateTime()),
        sa.Column('verification_rejection_reason', sa.Text()),
        sa.Column('token_balance', sa.Integer(), nullable=False, default=0),
        sa.Column('dt_balance', sa.Numeric(10, 2), nullable=False, default=0.0),
        sa.Column('stripe_customer_id', sa.String(500)),
        sa.Column('is_approved', sa.Boolean()),
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('approved_at', sa.DateTime()),
        sa.Column('teacher_certificate_url', sa.String(500)),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('locked_until', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('school_id', 'email', name='uq_user_school_email'),
        sa.Index('ix_users_email', 'email', postgresql_using='btree'),
        sa.Index('ix_users_school_id', 'school_id', postgresql_using='btree'),
        sa.Index('ix_users_school_role', 'school_id', 'role', postgresql_using='btree'),
        sa.Index('ix_users_role', 'role', postgresql_using='btree'),
    )

    # --- Table: ai_content_reports ---
    op.create_table(
        'ai_content_reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('message_id', sa.String(100)),
        sa.Column('conversation_id', sa.Integer()),
        sa.Column('reported_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='SET NULL')),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('details', sa.Text()),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('resolved_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('resolution_action', sa.Text()),
        sa.Column('resolution_response', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # --- Table: ai_conversations ---
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False, default='Nouvelle conversation'),
        sa.Column('subject', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_ai_conv_user_id', 'user_id', postgresql_using='btree'),
        sa.Index('ix_ai_conv_updated_at', 'updated_at', postgresql_using='btree'),
    )

    # --- Table: ai_usage_logs ---
    op.create_table(
        'ai_usage_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False, default=0),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('cost_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Index('ix_ai_logs_created_at', 'created_at', postgresql_using='btree'),
        sa.Index('ix_ai_logs_user_id', 'user_id', postgresql_using='btree'),
        sa.Index('ix_ai_logs_school_id', 'school_id', postgresql_using='btree'),
    )

    # --- Table: audit_logs ---
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('admin_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('admin_email', sa.String(255), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('target_type', sa.String(50)),
        sa.Column('target_id', sa.Integer()),
        sa.Column('details', sa.Text()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Index('ix_audit_admin_id', 'admin_id', postgresql_using='btree'),
        sa.Index('ix_audit_action', 'action', postgresql_using='btree'),
        sa.Index('ix_audit_created_at', 'created_at', postgresql_using='btree'),
    )

    # --- Table: cb_certificates ---
    op.create_table(
        'cb_certificates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('cb_course_contents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), sa.ForeignKey('cb_course_enrollments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('certificate_number', sa.String(50), nullable=False, unique=True),
        sa.Column('student_name', sa.String(255), nullable=False),
        sa.Column('course_name', sa.String(255), nullable=False),
        sa.Column('issue_date', sa.DateTime(), nullable=False),
        sa.Column('expiry_date', sa.DateTime()),
        sa.Column('status', sa.String(10), nullable=False, default='ready'),
        sa.Column('pdf_url', sa.String(500)),
        sa.Column('verification_code', sa.String(100), nullable=False, unique=True),
        sa.Column('grade', sa.Float()),
        sa.Column('completion_percent', sa.Integer(), nullable=False, default=0),
        sa.UniqueConstraint('certificate_number'),
        sa.UniqueConstraint('student_id', 'course_id', name='uq_cb_cert_student_course'),
        sa.UniqueConstraint('verification_code'),
    )

    # --- Table: cb_lessons ---
    op.create_table(
        'cb_lessons',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('chapter_id', sa.Integer(), sa.ForeignKey('cb_chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('lesson_type', sa.String(10), nullable=False, default='text'),
        sa.Column('content_text', sa.Text()),
        sa.Column('content_html', sa.Text()),
        sa.Column('video_url', sa.String(500)),
        sa.Column('video_duration_seconds', sa.Integer()),
        sa.Column('video_thumbnail_url', sa.String(500)),
        sa.Column('pdf_url', sa.String(500)),
        sa.Column('pdf_page_count', sa.Integer()),
        sa.Column('image_urls', sa.JSON()),
        sa.Column('link_url', sa.String(500)),
        sa.Column('link_title', sa.String(255)),
        sa.Column('order', sa.Integer(), nullable=False, default=0),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, default=0),
        sa.Column('is_free', sa.Boolean(), nullable=False, default=False),
        sa.Column('requires_enrollment', sa.Boolean(), nullable=False, default=True),
        sa.Column('ai_generated', sa.Boolean(), nullable=False, default=False),
        sa.Column('ai_prompt', sa.Text()),
        sa.Column('ai_model', sa.String(50)),
        sa.Column('tokens_used', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # --- Table: chapter_pathways ---
    op.create_table(
        'chapter_pathways',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('matiere_id', sa.Integer(), sa.ForeignKey('matieres.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nom', sa.String(200), nullable=False),
        sa.Column('ordre', sa.Integer(), nullable=False, default=0),
        sa.Index('ix_chapter_pathways_matiere', 'matiere_id', postgresql_using='btree'),
    )

    # --- Table: courses ---
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uuid', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('modified_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('short_description', sa.String(500)),
        sa.Column('description', sa.Text()),
        sa.Column('thumbnail_url', sa.String(500)),
        sa.Column('cover_url', sa.String(500)),
        sa.Column('slug', sa.String(255), unique=True),
        sa.Column('language', sa.String(10), default='fr'),
        sa.Column('prerequisites', sa.Text()),
        sa.Column('learning_objectives', sa.Text()),
        sa.Column('visibility', sa.String(20), nullable=False, default='private'),
        sa.Column('enrollment_type', sa.String(20), default='open'),
        sa.Column('owner_type', sa.String(30), nullable=False, default='school'),
        sa.Column('owner_id', sa.Integer()),
        sa.Column('price', sa.Numeric(10, 2)),
        sa.Column('currency', sa.String(10), nullable=False, default='TND'),
        sa.Column('commission_rate', sa.Numeric(5, 2)),
        sa.Column('price_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('price_dt', sa.Float(), nullable=False, default=0.0),
        sa.Column('category', sa.String(100)),
        sa.Column('level', sa.String(50)),
        sa.Column('niveau_scolaire', sa.String(50)),
        sa.Column('tags', sa.JSON()),
        sa.Column('status', sa.String(9), nullable=False, default='draft'),
        sa.Column('is_published', sa.Boolean(), nullable=False, default=False),
        sa.Column('max_students', sa.Integer()),
        sa.Column('pedagogical_status', sa.String(30), nullable=False, default='draft'),
        sa.Column('validated_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('validated_at', sa.DateTime()),
        sa.Column('validated_by_role', sa.String(30)),
        sa.Column('total_modules', sa.Integer(), nullable=False, default=0),
        sa.Column('total_lessons', sa.Integer(), nullable=False, default=0),
        sa.Column('total_duration_minutes', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('start_date', sa.DateTime()),
        sa.Column('end_date', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime()),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('uuid'),
        sa.Index('ix_courses_school_id', 'school_id', postgresql_using='btree'),
        sa.Index('ix_courses_school_status', 'school_id', 'status', postgresql_using='btree'),
        sa.Index('ix_courses_author_id', 'author_id', postgresql_using='btree'),
        sa.Index('ix_courses_status', 'status', postgresql_using='btree'),
    )

    # --- Table: documents ---
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uuid', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('uploader_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_url', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(50)),
        sa.Column('faiss_vector_id', sa.String(255)),
        sa.Column('status', sa.String(10), nullable=False, default='pending'),
        sa.Column('chunk_count', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('processed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('uuid'),
        sa.Index('ix_documents_uploader_id', 'uploader_id', postgresql_using='btree'),
        sa.Index('ix_documents_school_id', 'school_id', postgresql_using='btree'),
    )

    # --- Table: learning_goals ---
    op.create_table(
        'learning_goals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('matiere', sa.String(100)),
        sa.Column('horizon', sa.String(20), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('target_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(30), nullable=False, default='auto_generated'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_learning_goals_period', 'period_start', 'period_end', postgresql_using='btree'),
        sa.Index('ix_learning_goals_user_id', 'user_id', postgresql_using='btree'),
        sa.Index('ix_learning_goals_horizon', 'horizon', postgresql_using='btree'),
    )

    # --- Table: messages ---
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uuid', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('receiver_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('type', sa.String(11), nullable=False, default='direct'),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('target_audience', sa.String(50)),
        sa.Column('recipient_role', sa.String(20)),
        sa.Column('is_official_observation', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('read_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('uuid'),
        sa.Index('ix_messages_school_id', 'school_id', postgresql_using='btree'),
        sa.Index('ix_messages_sender_id', 'sender_id', postgresql_using='btree'),
        sa.Index('ix_messages_receiver_id', 'receiver_id', postgresql_using='btree'),
    )

    # --- Table: parent_enfants ---
    op.create_table(
        'parent_enfants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('parent_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('eleve_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date_creation', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('parent_user_id', 'eleve_id', name='uq_parent_eleve'),
        sa.Index('ix_parent_enfant_eleve', 'eleve_id', postgresql_using='btree'),
        sa.Index('ix_parent_enfant_parent', 'parent_user_id', postgresql_using='btree'),
    )

    # --- Table: password_reset_tokens ---
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Index('ix_password_reset_user', 'user_id', postgresql_using='btree'),
        sa.Index('ix_password_reset_tokens_token', 'token', unique=True, postgresql_using='btree'),
    )

    # --- Table: payments ---
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='TND'),
        sa.Column('status', sa.String(9), nullable=False, default='pending'),
        sa.Column('stripe_session_id', sa.String(500), unique=True),
        sa.Column('stripe_payment_intent', sa.String(500)),
        sa.Column('subscription_months', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('stripe_session_id'),
        sa.Index('ix_payment_user_id', 'user_id', postgresql_using='btree'),
        sa.Index('ix_payment_stripe_session_id', 'stripe_session_id', unique=True, postgresql_using='btree'),
    )

    # --- Table: placement_tests ---
    op.create_table(
        'placement_tests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('matiere', sa.String(100), nullable=False),
        sa.Column('niveau', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255)),
        sa.Column('questions', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # --- Table: progress ---
    op.create_table(
        'progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_id', sa.Integer(), sa.ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='not_started'),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, default=0),
        sa.Column('score', sa.Float()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_progress_user_lesson', 'user_id', 'lesson_id', unique=True, postgresql_using='btree'),
        sa.Index('ix_progress_user_id', 'user_id', postgresql_using='btree'),
        sa.Index('ix_progress_lesson_id', 'lesson_id', postgresql_using='btree'),
    )

    # --- Table: quiz_answers ---
    op.create_table(
        'quiz_answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('attempt_id', sa.Integer(), sa.ForeignKey('quiz_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('selected_option_ids', sa.Text()),
        sa.Column('text_answer', sa.Text()),
        sa.Column('is_correct', sa.Boolean()),
        sa.Column('points_awarded', sa.Integer(), nullable=False, default=0),
        sa.Column('answered_at', sa.DateTime(), nullable=False),
        sa.Index('ix_quiz_answers_attempt_id', 'attempt_id', postgresql_using='btree'),
    )

    # --- Table: quiz_options ---
    op.create_table(
        'quiz_options',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, default=False),
        sa.Column('order_index', sa.Integer(), nullable=False, default=0),
        sa.Index('ix_quiz_options_question_id', 'question_id', postgresql_using='btree'),
    )

    # --- Table: responsables_pedagogiques ---
    op.create_table(
        'responsables_pedagogiques',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('specialite_id', sa.Integer(), sa.ForeignKey('specialites_pedagogiques.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('user_id', 'specialite_id', name='uq_user_specialite'),
    )

    # --- Table: specialite_pedagogique_matieres ---
    op.create_table(
        'specialite_pedagogique_matieres',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('specialite_id', sa.Integer(), sa.ForeignKey('specialites_pedagogiques.id', ondelete='CASCADE'), nullable=False),
        sa.Column('matiere_id', sa.Integer(), sa.ForeignKey('matieres.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('specialite_id', 'matiere_id', name='uq_specialite_matiere'),
    )

    # --- Table: student_badges ---
    op.create_table(
        'student_badges',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('eleve_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('badge_id', sa.Integer(), sa.ForeignKey('badge_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date_obtention', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('eleve_id', 'badge_id', name='uq_student_badge'),
        sa.Index('ix_student_badges_eleve', 'eleve_id', postgresql_using='btree'),
    )

    # --- Table: student_rankings ---
    op.create_table(
        'student_rankings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('eleve_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('matiere_id', sa.Integer(), sa.ForeignKey('matieres.id', ondelete='SET NULL')),
        sa.Column('palier', sa.String(20), nullable=False),
        sa.Column('points_total', sa.Integer(), nullable=False, default=0),
        sa.Column('rang', sa.Integer()),
        sa.Column('date_calcul', sa.DateTime(), nullable=False),
        sa.Index('ix_student_rankings_eleve', 'eleve_id', postgresql_using='btree'),
        sa.Index('ix_student_rankings_palier', 'palier', postgresql_using='btree'),
        sa.Index('ix_student_rankings_matiere', 'matiere_id', postgresql_using='btree'),
    )

    # --- Table: student_streaks ---
    op.create_table(
        'student_streaks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('eleve_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date_jour', sa.Date(), nullable=False),
        sa.Column('streak_login', sa.Boolean(), nullable=False, default=False),
        sa.Column('streak_quiz', sa.Boolean(), nullable=False, default=False),
        sa.Column('streak_objectif', sa.Boolean(), nullable=False, default=False),
        sa.Column('points_jour', sa.Integer(), nullable=False, default=0),
        sa.UniqueConstraint('eleve_id', 'date_jour', name='uq_student_streak_day'),
        sa.Index('ix_student_streaks_eleve', 'eleve_id', postgresql_using='btree'),
    )

    # --- Table: study_packs ---
    op.create_table(
        'study_packs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('niveau_scolaire', sa.String(50), nullable=False),
        sa.Column('matieres', sa.JSON()),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, default='TND'),
        sa.Column('validity_duration_days', sa.Integer(), nullable=False, default=365),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('owner_type', sa.String(30), nullable=False, default='eduai_catalog'),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='SET NULL')),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_study_packs_niveau', 'niveau_scolaire', postgresql_using='btree'),
        sa.Index('ix_study_packs_status', 'status', postgresql_using='btree'),
    )

    # --- Table: subscriptions ---
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('token_packages.id', ondelete='SET NULL')),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('stripe_subscription_id', sa.String(255)),
        sa.Column('stripe_customer_id', sa.String(255)),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('ends_at', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
    )

    # --- Table: teacher_classes ---
    op.create_table(
        'teacher_classes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('code', sa.String(50)),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_tc_teacher_id', 'teacher_id', postgresql_using='btree'),
        sa.Index('ix_tc_school_id', 'school_id', postgresql_using='btree'),
    )

    # --- Table: teacher_registrations ---
    op.create_table(
        'teacher_registrations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('existing_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(500)),
        sa.Column('status', sa.String(8), nullable=False, default='pending'),
        sa.Column('rejection_reason', sa.Text()),
        sa.Column('certificate_url', sa.String(500)),
        sa.Column('cv_url', sa.String(500)),
        sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('reviewed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_teacher_reg_school_id', 'school_id', postgresql_using='btree'),
    )

    # --- Table: transactions ---
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uuid', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(17), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(5), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('reference_id', sa.String(255)),
        sa.Column('status', sa.String(50), nullable=False, default='completed'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('uuid'),
        sa.Index('ix_transactions_user_id', 'user_id', postgresql_using='btree'),
        sa.Index('ix_transactions_school_id', 'school_id', postgresql_using='btree'),
        sa.Index('ix_transactions_created_at', 'created_at', postgresql_using='btree'),
    )

    # --- Table: wallet_transactions ---
    op.create_table(
        'wallet_transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pool', sa.String(16), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('feature', sa.String(11)),
        sa.Column('related_request_id', sa.String(200)),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.JSON()),
        sa.Index('ix_wallet_tx_user_id', 'user_id', postgresql_using='btree'),
        sa.Index('ix_wallet_tx_user_pool', 'user_id', 'pool', postgresql_using='btree'),
        sa.Index('ix_wallet_tx_created_at', 'created_at', postgresql_using='btree'),
    )

    # --- Table: ai_chat_messages ---
    op.create_table(
        'ai_chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('detected_language', sa.String(10)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Index('ix_ai_msg_conv_id', 'conversation_id', postgresql_using='btree'),
    )

    # --- Table: cb_lesson_progress ---
    op.create_table(
        'cb_lesson_progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('enrollment_id', sa.Integer(), sa.ForeignKey('cb_course_enrollments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_id', sa.Integer(), sa.ForeignKey('cb_lessons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='not_started'),
        sa.Column('video_progress_seconds', sa.Integer(), default=0),
        sa.Column('video_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('content_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('quiz_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('quiz_passed', sa.Boolean()),
        sa.Column('quiz_score', sa.Float()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, default=0),
        sa.UniqueConstraint('enrollment_id', 'lesson_id', name='uq_cb_enrollment_lesson'),
    )

    # --- Table: cb_quizzes ---
    op.create_table(
        'cb_quizzes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('lesson_id', sa.Integer(), sa.ForeignKey('cb_lessons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('time_limit_minutes', sa.Integer()),
        sa.Column('passing_score_percent', sa.Integer(), nullable=False, default=70),
        sa.Column('shuffle_questions', sa.Boolean(), nullable=False, default=False),
        sa.Column('shuffle_options', sa.Boolean(), nullable=False, default=False),
        sa.Column('show_results', sa.Boolean(), nullable=False, default=True),
        sa.Column('show_correct_answers', sa.Boolean(), nullable=False, default=True),
        sa.Column('allow_retakes', sa.Boolean(), nullable=False, default=True),
        sa.Column('max_attempts', sa.Integer()),
        sa.Column('total_points', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # --- Table: cb_video_watch_progress ---
    op.create_table(
        'cb_video_watch_progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('enrollment_id', sa.Integer(), sa.ForeignKey('cb_course_enrollments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_id', sa.Integer(), sa.ForeignKey('cb_lessons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('current_position_seconds', sa.Integer(), nullable=False, default=0),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, default=0),
        sa.Column('percent_watched', sa.Float(), nullable=False, default=0.0),
        sa.Column('last_watched_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('enrollment_id', 'lesson_id', name='uq_cb_video_enrollment_lesson'),
    )

    # --- Table: class_course_access ---
    op.create_table(
        'class_course_access',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('class_id', sa.Integer(), sa.ForeignKey('teacher_classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Index('ix_cca_course_id', 'course_id', postgresql_using='btree'),
        sa.Index('ix_cca_class_course', 'class_id', 'course_id', unique=True, postgresql_using='btree'),
        sa.Index('ix_cca_class_id', 'class_id', postgresql_using='btree'),
    )

    # --- Table: classrooms ---
    op.create_table(
        'classrooms',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uuid', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('invite_code', sa.String(20), nullable=False, unique=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('max_students', sa.Integer(), nullable=False, default=30),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('invite_code'),
        sa.UniqueConstraint('uuid'),
    )

    # --- Table: course_enrollments ---
    op.create_table(
        'course_enrollments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(9), nullable=False, default='active'),
        sa.Column('progress_percent', sa.Integer(), nullable=False, default=0),
        sa.Column('enrolled_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.UniqueConstraint('student_id', 'course_id', name='uq_student_course'),
        sa.Index('ix_enrollments_status', 'status', postgresql_using='btree'),
        sa.Index('ix_enrollments_student_id', 'student_id', postgresql_using='btree'),
        sa.Index('ix_enrollments_course_id', 'course_id', postgresql_using='btree'),
    )

    # --- Table: course_purchases ---
    op.create_table(
        'course_purchases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, default='TND'),
        sa.Column('platform_fee', sa.Numeric(10, 2), nullable=False, default=0.0),
        sa.Column('teacher_revenue', sa.Numeric(10, 2), nullable=False, default=0.0),
        sa.Column('commission_rate_applied', sa.Numeric(5, 2)),
        sa.Column('transaction_id', sa.String(255)),
        sa.Column('refunded', sa.Boolean(), nullable=False, default=False),
        sa.Column('refund_reason', sa.Text()),
        sa.Column('refunded_at', sa.DateTime()),
        sa.Column('purchased_at', sa.DateTime(), nullable=False),
        sa.Index('ix_purchases_course_id', 'course_id', postgresql_using='btree'),
        sa.Index('ix_purchases_student_id', 'student_id', postgresql_using='btree'),
        sa.Index('ix_purchases_student_course', 'student_id', 'course_id', unique=True, postgresql_using='btree'),
    )

    # --- Table: historiques_scores ---
    op.create_table(
        'historiques_scores',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('eleve_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chapitre_id', sa.Integer(), sa.ForeignKey('chapter_pathways.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('quizzes.id', ondelete='SET NULL')),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Index('ix_historiques_scores_eleve_chapitre', 'eleve_id', 'chapitre_id', postgresql_using='btree'),
    )

    # --- Table: modules ---
    op.create_table(
        'modules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_modules_course_id', 'course_id', postgresql_using='btree'),
    )

    # --- Table: notions ---
    op.create_table(
        'notions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('chapitre_id', sa.Integer(), sa.ForeignKey('chapter_pathways.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nom', sa.String(200), nullable=False),
        sa.Column('ordre', sa.Integer(), nullable=False, default=0),
        sa.Index('ix_notions_chapitre', 'chapitre_id', postgresql_using='btree'),
    )

    # --- Table: pack_purchases ---
    op.create_table(
        'pack_purchases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('pack_id', sa.Integer(), sa.ForeignKey('study_packs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('purchaser_type', sa.String(20), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE')),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('amount_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, default='TND'),
        sa.Column('transaction_id', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Index('ix_pack_purchases_valid_until', 'valid_until', postgresql_using='btree'),
        sa.Index('ix_pack_purchases_student_id', 'student_id', postgresql_using='btree'),
        sa.Index('ix_pack_purchases_school_id', 'school_id', postgresql_using='btree'),
        sa.Index('ix_pack_purchases_status', 'status', postgresql_using='btree'),
        sa.Index('ix_pack_purchases_pack_id', 'pack_id', postgresql_using='btree'),
    )

    # --- Table: pedagogical_escalations ---
    op.create_table(
        'pedagogical_escalations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='SET NULL')),
        sa.Column('escalated_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('details', sa.Text()),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('resolved_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('resolution', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # --- Table: placement_test_results ---
    op.create_table(
        'placement_test_results',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('placement_test_id', sa.Integer(), sa.ForeignKey('placement_tests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('competency_level', sa.String(30), nullable=False),
        sa.Column('answers', sa.JSON()),
        sa.Column('score', sa.Float()),
        sa.Column('completed_at', sa.DateTime(), nullable=False),
    )

    # --- Table: profils_assimilation ---
    op.create_table(
        'profils_assimilation',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('eleve_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chapitre_id', sa.Integer(), sa.ForeignKey('chapter_pathways.id', ondelete='CASCADE'), nullable=False),
        sa.Column('niveau_assimilation_courant', sa.String(20), nullable=False),
        sa.Column('source_changement', sa.String(30), nullable=False),
        sa.Column('score_declencheur', sa.Float()),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('statut_validation', sa.String(30), nullable=False, default='auto_applique'),
        sa.Index('ix_profils_assimilation_eleve', 'eleve_id', postgresql_using='btree'),
        sa.Index('ix_profils_assimilation_chapitre', 'chapitre_id', postgresql_using='btree'),
        sa.Index('ix_profils_assimilation_eleve_chapitre', 'eleve_id', 'chapitre_id', postgresql_using='btree'),
    )

    # --- Table: responsable_niveaux_etude ---
    op.create_table(
        'responsable_niveaux_etude',
        sa.Column('responsable_id', sa.Integer(), sa.ForeignKey('responsables_pedagogiques.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('niveau_etude_id', sa.Integer(), sa.ForeignKey('niveaux_etude.id', ondelete='CASCADE'), primary_key=True),
    )

    # --- Table: school_course_access ---
    op.create_table(
        'school_course_access',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('purchased_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('granted_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('price_paid_dt', sa.Numeric(10, 2), default=0.0),
        sa.Index('ix_sca_course_id', 'course_id', postgresql_using='btree'),
        sa.Index('ix_sca_school_course', 'school_id', 'course_id', unique=True, postgresql_using='btree'),
        sa.Index('ix_sca_school_id', 'school_id', postgresql_using='btree'),
    )

    # --- Table: student_enrollments ---
    op.create_table(
        'student_enrollments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', sa.Integer(), sa.ForeignKey('teacher_classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('enrolled_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Index('ix_se_class_id', 'class_id', postgresql_using='btree'),
        sa.Index('ix_se_student_id', 'student_id', postgresql_using='btree'),
        sa.Index('ix_se_student_class', 'student_id', 'class_id', unique=True, postgresql_using='btree'),
    )

    # --- Table: assignments ---
    op.create_table(
        'assignments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('classroom_id', sa.Integer(), sa.ForeignKey('classrooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('instructions', sa.Text()),
        sa.Column('max_score', sa.Integer(), nullable=False, default=100),
        sa.Column('due_date', sa.DateTime()),
        sa.Column('allow_late_submission', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Index('ix_assignments_classroom_id', 'classroom_id', postgresql_using='btree'),
    )

    # --- Table: cb_quiz_attempts ---
    op.create_table(
        'cb_quiz_attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('cb_quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='in_progress'),
        sa.Column('score', sa.Float()),
        sa.Column('score_percent', sa.Float()),
        sa.Column('correct_count', sa.Integer()),
        sa.Column('total_count', sa.Integer()),
        sa.Column('passed', sa.Boolean()),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('graded_at', sa.DateTime()),
    )

    # --- Table: cb_quiz_questions ---
    op.create_table(
        'cb_quiz_questions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('cb_quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(15), nullable=False, default='multiple_choice'),
        sa.Column('points', sa.Integer(), nullable=False, default=1),
        sa.Column('explanation', sa.Text()),
        sa.Column('order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # --- Table: classroom_enrollments ---
    op.create_table(
        'classroom_enrollments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('classroom_id', sa.Integer(), sa.ForeignKey('classrooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(9), nullable=False, default='active'),
        sa.Column('role', sa.String(50), nullable=False, default='student'),
        sa.Column('enrolled_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('student_id', 'classroom_id', name='uq_student_classroom'),
    )

    # --- Table: contenus_notion ---
    op.create_table(
        'contenus_notion',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('notion_id', sa.Integer(), sa.ForeignKey('notions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('niveau_assimilation', sa.String(20), nullable=False),
        sa.Column('type_ressource', sa.String(30), nullable=False),
        sa.Column('contenu', sa.Text(), nullable=False),
        sa.Column('enseignant_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('statut_pedagogique', sa.String(10), nullable=False, default='a'),
        sa.Column('statut_validation_pedagogique', sa.String(20), nullable=False, default='en_attente'),
        sa.Column('valide_par', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('date_validation', sa.DateTime()),
        sa.Column('commentaire_rejet', sa.Text()),
        sa.Index('ix_contenus_notion_notion', 'notion_id', postgresql_using='btree'),
        sa.Index('ix_contenus_notion_niveau', 'niveau_assimilation', postgresql_using='btree'),
    )

    # --- Table: notifications_reorientation ---
    op.create_table(
        'notifications_reorientation',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profil_assimilation_id', sa.Integer(), sa.ForeignKey('profils_assimilation.id', ondelete='CASCADE'), nullable=False),
        sa.Column('enseignant_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date_notification', sa.DateTime(), nullable=False),
        sa.Column('date_limite_action', sa.DateTime(), nullable=False),
        sa.Column('action_prise', sa.String(20), nullable=False, default='aucune'),
        sa.Index('ix_notifications_reorientation_enseignant', 'enseignant_id', postgresql_using='btree'),
        sa.Index('ix_notifications_reorientation_profil', 'profil_assimilation_id', postgresql_using='btree'),
    )

    # --- Table: teacher_reassignments ---
    op.create_table(
        'teacher_reassignments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('class_id', sa.Integer(), sa.ForeignKey('classrooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_teacher_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('new_teacher_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime()),
        sa.Column('reason', sa.Text()),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # --- Table: cb_quiz_options ---
    op.create_table(
        'cb_quiz_options',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('cb_quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # --- Table: cb_student_answers ---
    op.create_table(
        'cb_student_answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('attempt_id', sa.Integer(), sa.ForeignKey('cb_quiz_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('cb_quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selected_option_ids', sa.JSON()),
        sa.Column('text_answer', sa.Text()),
        sa.Column('is_correct', sa.Boolean()),
        sa.Column('points_earned', sa.Integer(), default=0),
        sa.Column('answered_at', sa.DateTime(), nullable=False),
    )

    # --- Table: submissions ---
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('assignment_id', sa.Integer(), sa.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text()),
        sa.Column('file_url', sa.String(500)),
        sa.Column('ai_score', sa.Integer()),
        sa.Column('ai_feedback', sa.Text()),
        sa.Column('tokens_used', sa.Integer()),
        sa.Column('is_late', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_graded', sa.Boolean(), nullable=False, default=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('graded_at', sa.DateTime()),
        sa.Index('ix_submissions_assignment_id', 'assignment_id', postgresql_using='btree'),
        sa.Index('ix_submissions_student_id', 'student_id', postgresql_using='btree'),
    )

    # --- Table: cb_correct_answers ---
    op.create_table(
        'cb_correct_answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('cb_quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('option_id', sa.Integer(), sa.ForeignKey('cb_quiz_options.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )



def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("cb_correct_answers")
    op.drop_table("submissions")
    op.drop_table("cb_student_answers")
    op.drop_table("cb_quiz_options")
    op.drop_table("teacher_reassignments")
    op.drop_table("notifications_reorientation")
    op.drop_table("contenus_notion")
    op.drop_table("classroom_enrollments")
    op.drop_table("cb_quiz_questions")
    op.drop_table("cb_quiz_attempts")
    op.drop_table("assignments")
    op.drop_table("student_enrollments")
    op.drop_table("school_course_access")
    op.drop_table("responsable_niveaux_etude")
    op.drop_table("profils_assimilation")
    op.drop_table("placement_test_results")
    op.drop_table("pedagogical_escalations")
    op.drop_table("pack_purchases")
    op.drop_table("notions")
    op.drop_table("modules")
    op.drop_table("historiques_scores")
    op.drop_table("course_purchases")
    op.drop_table("course_enrollments")
    op.drop_table("classrooms")
    op.drop_table("class_course_access")
    op.drop_table("cb_video_watch_progress")
    op.drop_table("cb_quizzes")
    op.drop_table("cb_lesson_progress")
    op.drop_table("ai_chat_messages")
    op.drop_table("wallet_transactions")
    op.drop_table("transactions")
    op.drop_table("teacher_registrations")
    op.drop_table("teacher_classes")
    op.drop_table("subscriptions")
    op.drop_table("study_packs")
    op.drop_table("student_streaks")
    op.drop_table("student_rankings")
    op.drop_table("student_badges")
    op.drop_table("specialite_pedagogique_matieres")
    op.drop_table("responsables_pedagogiques")
    op.drop_table("quiz_options")
    op.drop_table("quiz_answers")
    op.drop_table("progress")
    op.drop_table("placement_tests")
    op.drop_table("payments")
    op.drop_table("password_reset_tokens")
    op.drop_table("parent_enfants")
    op.drop_table("messages")
    op.drop_table("learning_goals")
    op.drop_table("documents")
    op.drop_table("courses")
    op.drop_table("chapter_pathways")
    op.drop_table("cb_lessons")
    op.drop_table("cb_certificates")
    op.drop_table("audit_logs")
    op.drop_table("ai_usage_logs")
    op.drop_table("ai_conversations")
    op.drop_table("ai_content_reports")
    op.drop_table("users")
    op.drop_table("token_packages")
    op.drop_table("specialites_pedagogiques")
    op.drop_table("quiz_questions")
    op.drop_table("quiz_attempts")
    op.drop_table("platform_settings")
    op.drop_table("matieres")
    op.drop_table("cb_course_enrollments")
    op.drop_table("cb_chapters")
    op.drop_table("schools")
    op.drop_table("quizzes")
    op.drop_table("notes")
    op.drop_table("niveaux_etude")
    op.drop_table("media_assets")
    op.drop_table("lessons")
    op.drop_table("lesson_progress")
    op.drop_table("certificates")
    op.drop_table("cb_course_contents")
    op.drop_table("bookmarks")
    op.drop_table("badge_definitions")
