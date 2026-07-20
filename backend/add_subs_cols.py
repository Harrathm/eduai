import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from app.db_utils import get_connection

conn = get_connection()
cur = conn.cursor()

adds = [
    ("plans", "ALTER TABLE plans ADD COLUMN IF NOT EXISTS stripe_price_id VARCHAR(100)"),
    ("plans", "ALTER TABLE plans ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT true"),
    ("plans", "ALTER TABLE plans ADD COLUMN IF NOT EXISTS features JSON"),
    ("subscriptions", "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255)"),
    ("subscriptions", "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255)"),
    ("subscriptions", "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true"),
    ("subscriptions", "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS extra_data JSON"),
]

for table, sql in adds:
    cur.execute(sql)
    conn.commit()
    print(f"Added to {table}: {sql[:50]}...")

conn.close()
print("All subscription columns added!")