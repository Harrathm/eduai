from sqlalchemy import text
from app.db import SessionLocal

db = SessionLocal()
# Restore admin school roles
db.execute(text("UPDATE users SET role = 'ADMIN_SCHOOL' WHERE email = 'admin@pro-school.edu'"))
db.execute(text("UPDATE users SET role = 'ADMIN_SCHOOL' WHERE email = 'admin@tech-institute.edu'"))
db.execute(text("UPDATE users SET role = 'ADMIN_SCHOOL' WHERE email = 'admin@free-academy.edu'"))
db.execute(text("UPDATE users SET role = 'ADMIN_SCHOOL' WHERE email = 'admin@university.edu'"))
db.commit()
print('Restored admin school roles')

result = db.execute(text("SELECT email, role FROM users WHERE email LIKE 'admin@%'")).fetchall()
for r in result:
    print(r[0], ':', r[1])
db.close()