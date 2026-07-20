import sys
sys.path.insert(0, '.')
from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT email, role FROM users WHERE email = 'admin@demo-academy.edu'"))
    rows = result.fetchall()
    print("Admin user:", rows)