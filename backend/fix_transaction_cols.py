from sqlalchemy import text
from app.db import SessionLocal

db = SessionLocal()

# Check Transaction columns
result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'transactions' AND column_name = 'created_at'")).fetchone()
if not result:
    print("Adding created_at column to transactions...")
    db.execute(text("ALTER TABLE transactions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    db.commit()
    print("Done")
else:
    print("created_at already exists")

# Check Transaction has school_id
result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'transactions' AND column_name = 'school_id'")).fetchone()
if not result:
    print("Adding school_id column to transactions...")
    db.execute(text("ALTER TABLE transactions ADD COLUMN school_id INTEGER REFERENCES schools(id)"))
    db.commit()
    print("Done")
else:
    print("school_id already exists")

db.close()