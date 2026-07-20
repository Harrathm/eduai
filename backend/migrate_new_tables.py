import sys
sys.path.insert(0, 'E:\\system_educatif_tn\\RAG\\RAG_APP_new\\backend')

from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS teacher_registrations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                qualifications TEXT,
                experience_years INTEGER,
                status VARCHAR(50) DEFAULT 'pending',
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                school_id INTEGER NOT NULL
            )
        '''))
        print('Created teacher_registrations')
    except Exception as e:
        print(f'teacher_registrations: {e}')

    try:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS course_purchases (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
                amount_paid_tokens INTEGER DEFAULT 0,
                amount_paid_dt FLOAT DEFAULT 0,
                payment_method VARCHAR(50),
                transaction_id VARCHAR(255),
                purchased_at TIMESTAMP DEFAULT NOW(),
                school_id INTEGER NOT NULL
            )
        '''))
        print('Created course_purchases')
    except Exception as e:
        print(f'course_purchases: {e}')

    try:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                type VARCHAR(50) NOT NULL,
                amount FLOAT NOT NULL,
                currency VARCHAR(10) DEFAULT 'DT',
                description TEXT,
                reference_id VARCHAR(255),
                status VARCHAR(50) DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT NOW(),
                school_id INTEGER NOT NULL
            )
        '''))
        print('Created transactions')
    except Exception as e:
        print(f'transactions: {e}')

    try:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS token_packages (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                tokens INTEGER NOT NULL,
                price_dt FLOAT NOT NULL,
                bonus_tokens INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT true
            )
        '''))
        print('Created token_packages')
    except Exception as e:
        print(f'token_packages: {e}')

    try:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS lesson_media (
                id SERIAL PRIMARY KEY,
                lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
                type VARCHAR(50) NOT NULL,
                url VARCHAR(500) NOT NULL,
                title VARCHAR(255),
                description TEXT,
                order_index INTEGER DEFAULT 0,
                school_id INTEGER NOT NULL
            )
        '''))
        print('Created lesson_media')
    except Exception as e:
        print(f'lesson_media: {e}')

    conn.commit()
    print('All tables created!')