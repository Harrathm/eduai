"""Reset account lockout for all users."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai")

from app.db_utils import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("UPDATE users SET locked_until = NULL, failed_login_attempts = 0")
conn.commit()
print(f"Unlocked {cur.rowcount} accounts")
conn.close()
