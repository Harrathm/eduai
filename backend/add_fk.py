"""Add FK constraint for lessons.quiz_id"""
from app.db import engine
from sqlalchemy import text

with engine.begin() as conn:
    # Add FK to quizzes table
    try:
        conn.execute(text('ALTER TABLE lessons ADD CONSTRAINT fk_lessons_quiz FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE SET NULL'))
        print("FK added: lessons.quiz_id -> quizzes.id")
    except Exception as e:
        if "duplicate" in str(e).lower() or "exists" in str(e).lower():
            print("FK already exists")
        else:
            print(f"FK error (may be OK if no ref table): {e}")