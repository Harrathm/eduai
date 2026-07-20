import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
cursor = conn.cursor()

# Find the correct admin
cursor.execute("SELECT id, email, role FROM users WHERE email = 'admin@eduai.platform'")
admin = cursor.fetchone()
print(f"Current admin: {admin}")

# Delete all other admin users with this email
cursor.execute("DELETE FROM users WHERE email = 'admin@eduai.platform'")
print(f"Deleted old users")

# Insert the correct admin back with proper credentials
cursor.execute("""
    INSERT INTO users (email, hashed_password, full_name, role, is_active, is_approved, token_balance, dt_balance, school_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    "admin@eduai.platform",
    "pbkdf2:sha256:260000$random",  # placeholder - will be set by login
    "Platform Admin",
    "SUPER_ADMIN",
    True, True,
    100000, 10000.0,
    1
))

conn.commit()

# Check
cursor.execute("SELECT id, email, role FROM users WHERE email = 'admin@eduai.platform'")
print(f"After fix: {cursor.fetchone()}")

conn.close()

print("\nNow the password needs to be reset - please run the seed script again")