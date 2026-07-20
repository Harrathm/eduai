import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
cur = conn.cursor()
tables = ['schools', 'users', 'classes', 'courses', 'modules', 'lessons', 'assignments', 'submissions']
for table in tables:
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'created_at'")
    has_created = bool(cur.fetchone())
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'updated_at'")
    has_updated = bool(cur.fetchone())
    print(f'{table}: created_at={has_created}, updated_at={has_updated}')

cur.execute("SELECT email, role, full_name FROM users LIMIT 5")
for r in cur.fetchall():
    print(r)
conn.close()