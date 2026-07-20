from sqlalchemy import text
from app.db import SessionLocal

db = SessionLocal()
result = db.execute(text("SELECT email, role FROM users WHERE email LIKE '%admin@%'")).fetchall()
for r in result:
    print(r[0], "->", r[1])
db.close()