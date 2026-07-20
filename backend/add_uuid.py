import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("ALTER TABLE users ADD COLUMN uuid UUID")
print("Added uuid column")

cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
cols = [row[0] for row in cursor.fetchall()]
print("Updated columns:", cols)