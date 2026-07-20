import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
cursor = conn.cursor()

# Check admin
cursor.execute("SELECT id, email, role FROM users WHERE email = 'admin@eduai.platform'")
print("Admin:", cursor.fetchall())

# Check all users
cursor.execute("SELECT id, email, role FROM users ORDER BY id")
print("\nAll users:")
for u in cursor.fetchall():
    print(f"  {u}")

conn.close()