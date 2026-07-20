from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, email, role FROM users WHERE role = 'SUPER_ADMIN' OR role = 'ADMIN_SCHOOL' LIMIT 10"))
    for row in result:
        print(row)