"""
Migration script - Add missing LMS columns and create LMS tables
"""
from sqlalchemy import text, inspect
from app.db import engine

def get_existing_columns(table):
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
        return {row[0] for row in result}

def add_column_if_not_exists(table, col_def):
    col_name = col_def.split()[0].strip('"')
    existing = get_existing_columns(table)
    if col_name not in existing:
        with engine.begin() as conn:
            conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {col_def}'))
            print(f"  + Added column: {col_name}")
    else:
        print(f"  = Already exists: {col_name}")

print("=== Adding missing columns to cb_lessons table ===")
lessons_cols = [
    'school_id INTEGER NOT NULL DEFAULT 1',
    'teacher_id INTEGER DEFAULT NULL',
    'video_url VARCHAR(500) DEFAULT NULL',
    'pdf_url VARCHAR(500) DEFAULT NULL',
    'image_urls TEXT DEFAULT NULL',
    'link_url VARCHAR(500) DEFAULT NULL',
    'link_title VARCHAR(255) DEFAULT NULL',
    'video_duration_seconds INTEGER DEFAULT NULL',
    'video_thumbnail_url VARCHAR(500) DEFAULT NULL',
    'document_url VARCHAR(500) DEFAULT NULL',
    'document_type VARCHAR(20) DEFAULT NULL',
    'quiz_id INTEGER DEFAULT NULL',
    'is_preview BOOLEAN NOT NULL DEFAULT FALSE',
    'content_html TEXT DEFAULT NULL',
    'completed_at TIMESTAMP DEFAULT NULL',
]
for c in lessons_cols:
    add_column_if_not_exists('cb_lessons', c)

print("\n=== Adding missing columns to modules table ===")
modules_cols = [
    'cover_url VARCHAR(500) DEFAULT NULL',
    'order_index INTEGER NOT NULL DEFAULT 0',
]
for c in modules_cols:
    add_column_if_not_exists('modules', c)

# ---- Create new LMS tables ----
print("\n=== Creating new LMS tables ===")

with engine.begin() as conn:
    # cb_chapters table (for LMS catalog - maps to modules conceptually but separate for LMS)
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS cb_chapters (
            id SERIAL PRIMARY KEY,
            course_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            cover_url VARCHAR(500),
            order_index INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    '''))
    print("  + Created: cb_chapters")

    # cb_quizzes table
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS cb_quizzes (
            id SERIAL PRIMARY KEY,
            lesson_id INTEGER,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            time_limit_seconds INTEGER,
            passing_score_percent INTEGER NOT NULL DEFAULT 70,
            max_attempts INTEGER,
            shuffle_questions BOOLEAN NOT NULL DEFAULT FALSE,
            shuffle_options BOOLEAN NOT NULL DEFAULT FALSE,
            show_results BOOLEAN NOT NULL DEFAULT TRUE,
            show_correct_answers BOOLEAN NOT NULL DEFAULT TRUE,
            total_points INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    '''))
    print("  + Created: cb_quizzes")

    # cb_quiz_questions table
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS cb_quiz_questions (
            id SERIAL PRIMARY KEY,
            quiz_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            question_type VARCHAR(20) NOT NULL DEFAULT 'mcq',
            points INTEGER NOT NULL DEFAULT 1,
            explanation TEXT,
            order_index INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    '''))
    print("  + Created: cb_quiz_questions")

    # cb_quiz_options table
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS cb_quiz_options (
            id SERIAL PRIMARY KEY,
            question_id INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL DEFAULT FALSE,
            order_index INTEGER NOT NULL DEFAULT 0
        )
    '''))
    print("  + Created: cb_quiz_options")

    # cb_quiz_attempts table
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS cb_quiz_attempts (
            id SERIAL PRIMARY KEY,
            quiz_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
            score DOUBLE PRECISION,
            score_percent DOUBLE PRECISION,
            correct_count INTEGER,
            total_count INTEGER,
            passed BOOLEAN,
            started_at TIMESTAMP NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMP,
            graded_at TIMESTAMP
        )
    '''))
    print("  + Created: cb_quiz_attempts")

    # cb_student_answers table
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS cb_student_answers (
            id SERIAL PRIMARY KEY,
            attempt_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            selected_option_ids TEXT,
            text_answer TEXT,
            is_correct BOOLEAN,
            points_awarded INTEGER NOT NULL DEFAULT 0,
            answered_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    '''))
    print("  + Created: cb_student_answers")

    # notes table
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            position INTEGER,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    '''))
    print("  + Created: notes")

    # bookmarks table
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            position_seconds INTEGER NOT NULL DEFAULT 0,
            note VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    '''))
    print("  + Created: bookmarks")

    # cb_lesson_progress table
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS cb_lesson_progress (
            id SERIAL PRIMARY KEY,
            enrollment_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'not_started',
            video_position_seconds INTEGER NOT NULL DEFAULT 0,
            video_completed BOOLEAN NOT NULL DEFAULT FALSE,
            content_completed BOOLEAN NOT NULL DEFAULT FALSE,
            quiz_completed BOOLEAN NOT NULL DEFAULT FALSE,
            quiz_passed BOOLEAN,
            quiz_score DOUBLE PRECISION,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            time_spent_seconds INTEGER NOT NULL DEFAULT 0,
            UNIQUE(enrollment_id, lesson_id)
        )
    '''))
    print("  + Created: cb_lesson_progress")

    # cb_certificates table
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS cb_certificates (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            enrollment_id INTEGER NOT NULL,
            certificate_number VARCHAR(50) NOT NULL UNIQUE,
            student_name VARCHAR(255) NOT NULL,
            course_name VARCHAR(255) NOT NULL,
            issue_date TIMESTAMP NOT NULL DEFAULT NOW(),
            expiry_date TIMESTAMP,
            status VARCHAR(20) NOT NULL DEFAULT 'ready',
            pdf_url VARCHAR(500),
            verification_code VARCHAR(100) NOT NULL UNIQUE,
            grade DOUBLE PRECISION,
            completion_percent INTEGER NOT NULL DEFAULT 0,
            UNIQUE(student_id, course_id)
        )
    '''))
    print("  + Created: cb_certificates")

print("\n=== Migration complete ===")

# Verify
with engine.connect() as conn:
    tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    print("Tables now:", sorted([r[0] for r in tables]))