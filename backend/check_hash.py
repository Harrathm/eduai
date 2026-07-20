import sys
sys.path.insert(0, '.')
import bcrypt
from app.db import get_db
from sqlalchemy import text

db_gen = get_db()
db = next(db_gen)

# Get full hash for admin
result = db.execute(text("SELECT email, hashed_password FROM users WHERE email = 'admin@demo-academy.edu'"))
row = result.fetchone()
if row:
    print(f"Email: {row[0]}")
    print(f"Full hash: {row[1]}")
    print(f"Hash length: {len(row[1])}")
    
    # Test bcrypt
    try:
        result_check = bcrypt.checkpw('password123'.encode(), row[1].encode())
        print(f"bcrypt check result: {result_check}")
    except Exception as e:
        print(f"bcrypt error: {e}")