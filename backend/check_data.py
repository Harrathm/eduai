import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
conn.autocommit = True
cursor = conn.cursor()

# Get all unique emails
cursor.execute("SELECT email FROM users GROUP BY email ORDER BY email")
emails = [row[0] for row in cursor.fetchall()]
print("Emails:", emails[:20])

# Get all schools
cursor.execute("SELECT id, name, domain FROM schools")
schools = cursor.fetchall()
print("\nSchools:", schools)