import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
cur = conn.cursor()

creates = [
    """CREATE TABLE IF NOT EXISTS ai_usage_logs (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        action VARCHAR(50) NOT NULL,
        tokens_used INTEGER DEFAULT 0,
        cost_usd FLOAT DEFAULT 0.0,
        school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS progress (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
        lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
        completed BOOLEAN DEFAULT false,
        completed_at TIMESTAMP,
        school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS quiz_questions (
        id SERIAL PRIMARY KEY,
        quiz_id INTEGER REFERENCES quizzes(id) ON DELETE CASCADE,
        text TEXT NOT NULL,
        type VARCHAR(20) DEFAULT 'mcq',
        points FLOAT DEFAULT 1.0,
        "order" INTEGER DEFAULT 0,
        school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS quiz_options (
        id SERIAL PRIMARY KEY,
        question_id INTEGER REFERENCES quiz_questions(id) ON DELETE CASCADE,
        text TEXT NOT NULL,
        is_correct BOOLEAN DEFAULT false,
        "order" INTEGER DEFAULT 0,
        school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS attempts (
        id SERIAL PRIMARY KEY,
        quiz_id INTEGER REFERENCES quizzes(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        score FLOAT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        finished_at TIMESTAMP,
        status VARCHAR(50) DEFAULT 'in_progress',
        school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS enrollments (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
        status VARCHAR(50) DEFAULT 'active',
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
        UNIQUE(school_id, user_id, class_id)
    )""",
]

for sql in creates:
    cur.execute(sql)
    conn.commit()

conn.close()
print("All new tables created!")