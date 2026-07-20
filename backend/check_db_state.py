from sqlalchemy import text
from app.db import SessionLocal

db = SessionLocal()
print("=== TABLES ===")
result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")).fetchall()
for r in result:
    print(r[0])

print("\n=== DATA COUNTS ===")
tables = ['users', 'schools', 'courses', 'transactions']
for t in tables:
    try:
        result = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"{t}: {result}")
    except Exception as e:
        print(f"{t}: ERROR - {e}")

db.close()