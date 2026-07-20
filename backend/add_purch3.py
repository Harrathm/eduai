from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE course_purchases ADD COLUMN IF NOT EXISTS currency VARCHAR(10)"))
    print('Added currency')
    conn.commit()
    print('Done')