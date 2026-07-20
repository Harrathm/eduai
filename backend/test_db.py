from app.db import get_db
from app.models import User
from sqlalchemy import text
from app.core.security import get_password_hash
from datetime import datetime

db = next(get_db())

# Method 1: SQLAlchemy query
user = db.query(User).filter(User.id == 86).first()
print(f"SQLAlchemy: {user}")

# Method 2: Raw SQL
result = db.execute(text("SELECT id, email FROM users WHERE id = 86")).first()
print(f"Raw SQL: {result}")

# Method 3: List some IDs
result = db.execute(text("SELECT id FROM users LIMIT 5")).fetchall()
print(f"First 5 IDs: {[r[0] for r in result]}")