import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection
from app.core.security import verify_password

conn = get_connection()
conn.autocommit = True
cursor = conn.cursor()
cursor.execute("SELECT email, hashed_password FROM users WHERE email = 'admin@eduai.platform'")
row = cursor.fetchone()
if row:
    print(f"Email: {row[0]}")
    print(f"Hash: {row[1][:20]}...")
    result = verify_password("password123", row[1])
    print(f"Password verification: {result}")