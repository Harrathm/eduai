import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("SELECT id, email, full_name, role, school_id FROM users LIMIT 10")
rows = cursor.fetchall()
print("Users:", rows)

cursor.execute("SELECT id, name, subdomain FROM schools LIMIT 10")
rows = cursor.fetchall()
print("Schools:", rows)