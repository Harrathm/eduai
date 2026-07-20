import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)
cur.execute('SELECT COUNT(*) FROM schools')
print('Schools:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM users')
print('Users:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM courses')
print('Courses:', cur.fetchone()[0])
conn.close()