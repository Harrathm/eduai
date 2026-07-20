from sqlalchemy import text
from app.db import SessionLocal

db = SessionLocal()
# Try different case
result1 = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'")).scalar()
result2 = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'ADMIN'")).scalar()
print('role=admin:', result1)
print('role=ADMIN:', result2)

if result2 > 0:
    db.execute(text("UPDATE users SET role = 'admin_school' WHERE role = 'ADMIN'"))
    db.commit()
    print('Updated ADMIN to admin_school')
else:
    print('No ADMIN found')

# Show final
result = db.execute(text("SELECT role, COUNT(*) FROM users GROUP BY role")).fetchall()
for r in result:
    print(r[0], ':', r[1])
db.close()