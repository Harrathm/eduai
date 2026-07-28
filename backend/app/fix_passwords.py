import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.db_utils import get_connection
from app.core.security import get_password_hash

conn = get_connection()
cur = conn.cursor()
password_hash = get_password_hash("password123")

cur.execute("UPDATE users SET hashed_password = %s", (password_hash,))
conn.commit()
print(f"Updated {cur.rowcount} users with correct password hash")
conn.close()