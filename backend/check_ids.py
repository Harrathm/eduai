import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
cursor = conn.cursor()

# Check both IDs
for uid in [25, 77]:
    cursor.execute("SELECT id, email, role, school_id FROM users WHERE id = %s", (uid,))
    user = cursor.fetchone()
    print(f"ID {uid}: {user}")

conn.close()