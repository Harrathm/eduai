import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
conn.autocommit = True
cursor = conn.cursor()

# Schools - add missing columns
try:
    cursor.execute("ALTER TABLE schools ADD COLUMN uuid UUID")
    print("Added uuid to schools")
except Exception as e:
    print(f"schools.uuid: {e}")

try:
    cursor.execute("ALTER TABLE schools ADD COLUMN logo_url VARCHAR(500)")
    print("Added logo_url to schools")
except Exception as e:
    print(f"schools.logo_url: {e}")

try:
    cursor.execute("ALTER TABLE schools ADD COLUMN primary_color VARCHAR(20)")
    print("Added primary_color to schools")
except Exception as e:
    print(f"schools.primary_color: {e}")

try:
    cursor.execute("ALTER TABLE schools ADD COLUMN subscription_expires_at TIMESTAMP")
    print("Added subscription_expires_at to schools")
except Exception as e:
    print(f"schools.subscription_expires_at: {e}")

try:
    cursor.execute("ALTER TABLE schools ADD COLUMN maintenance_mode BOOLEAN DEFAULT FALSE")
    print("Added maintenance_mode to schools")
except Exception as e:
    print(f"schools.maintenance_mode: {e}")

try:
    cursor.execute("ALTER TABLE schools ADD COLUMN allow_teacher_registration BOOLEAN DEFAULT TRUE")
    print("Added allow_teacher_registration to schools")
except Exception as e:
    print(f"schools.allow_teacher_registration: {e}")

try:
    cursor.execute("ALTER TABLE schools ADD COLUMN allow_new_signups BOOLEAN DEFAULT TRUE")
    print("Added allow_new_signups to schools")
except Exception as e:
    print(f"schools.allow_new_signups: {e}")

# Verify final schema
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'schools'")
cols = [r[0] for r in cursor.fetchall()]
print(f"\nSchools columns: {cols}")