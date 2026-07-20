import sys
sys.path.insert(0, '.')

# Test imports
from app.main import app
from app.db import get_db
from app.models import User
from app.core.security import verify_password

# Test db connection
db_gen = get_db()
db = next(db_gen)

# Test query
user = db.query(User).filter(User.email == "admin@demo-academy.edu").first()
print(f"User found: {user.email}")

# Test password
result = verify_password("password123", user.hashed_password)
print(f"Password valid: {result}")