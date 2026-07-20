from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS course_purchases (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                amount_paid INTEGER DEFAULT 0,
                currency VARCHAR(10) DEFAULT 'DTN',
                transaction_id VARCHAR(100),
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))
        print('Created course_purchases table')
    except Exception as e:
        print(f'Error: {e}')
    conn.commit()
    print('Done')