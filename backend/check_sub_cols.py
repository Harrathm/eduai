from sqlalchemy import text
from app.db import SessionLocal

db = SessionLocal()
result = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'subscriptions'")).fetchall()
print("Subscription columns:")
for r in result:
    print(f"{r[0]}: {r[1]}")
db.close()