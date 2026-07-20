from app.db import engine
from sqlalchemy import text
with engine.begin() as conn:
    # Check lessons columns
    cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'lessons'")).fetchall()
    print('lessons columns:', [c[0] for c in cols])
    # Check FK constraints
    fks = conn.execute(text("""
        SELECT tc.constraint_name, kcu.column_name, ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_name = 'lessons' AND tc.constraint_type = 'FOREIGN KEY'
    """)).fetchall()
    print('FKs:', fks)
    # Check quizzes columns
    qcols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'quizzes'")).fetchall()
    print('quizzes columns:', [c[0] for c in qcols])