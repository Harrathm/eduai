from sqlalchemy import text
from app.db import SessionLocal

db = SessionLocal()
result = db.execute(text("SELECT role FROM users GROUP BY role")).fetchall()
print('Roles in DB:', [r[0] for r in result])

result2 = db.execute(text("SELECT role, COUNT(*) FROM users GROUP BY role")).fetchall()
for r in result2:
    print(r[0], ':', r[1])
db.close()