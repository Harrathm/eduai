import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
cur = conn.cursor()

# Check subscriptions table
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'subscriptions' ORDER BY ordinal_position")
print("subscriptions columns:", [r[0] for r in cur.fetchall()])

# Check plans table
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'plans' ORDER BY ordinal_position")
print("plans columns:", [r[0] for r in cur.fetchall()])

# Check data
cur.execute("SELECT name, price, stripe_price_id, active FROM plans")
for r in cur.fetchall():
    print(f"Plan: {r[0]} - ${r[1]/100}/mo - active={r[3]}")

cur.execute("SELECT COUNT(*) FROM subscriptions")
print(f"Subscriptions: {cur.fetchone()[0]}")

conn.close()