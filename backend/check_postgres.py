import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
cursor = conn.cursor()

print("=== Users in PostgreSQL ===")
cursor.execute("SELECT email, role, school_id FROM users ORDER BY email")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} (school_id={row[2]})")

print("\n=== Schools in PostgreSQL ===")
cursor.execute("SELECT id, name, slug FROM schools ORDER BY id")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} ({row[2]})")

print("\n=== Courses in PostgreSQL ===")
cursor.execute("SELECT id, title, school_id FROM courses ORDER BY id")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} (school_id={row[2]})")

conn.close()