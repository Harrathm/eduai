import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.db_utils import get_connection

conn = get_connection()
cur = conn.cursor()
password_hash = "$2b$12$395V7vty/nIwNJuyUUZrsOwMNJCqmlJMXrXFNyJzqdhMbvZDvgp66"

cur.execute("UPDATE users SET hashed_password = %s", (password_hash,))
conn.commit()
print(f"Updated {cur.rowcount} users with correct password hash")
conn.close()