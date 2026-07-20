import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
conn.autocommit = True
cursor = conn.cursor()

tables = ['course_enrollments', 'modules', 'lessons', 'course_purchases']
for t in tables:
    try:
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'")
        cols = [r[0] for r in cursor.fetchall()]
        print(f"{t}: {cols}")
    except Exception as e:
        print(f"{t}: ERROR - {e}")