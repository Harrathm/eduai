from app.db import engine
from sqlalchemy import text
from app.core.security import get_password_hash

with engine.connect() as conn:
    conn.execute(text("UPDATE users SET hashed_password = :pwd WHERE email = 'admin@eduai.platform'"), {"pwd": get_password_hash("password123")})
    conn.commit()
    print("Password updated for admin@eduai.platform")