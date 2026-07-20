import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import text
from app.db import engine

MIGRATION_SQL = [
    # Wallet transactions table
    """
    CREATE TABLE IF NOT EXISTS wallet_transactions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        pool VARCHAR(30) NOT NULL,
        amount INTEGER NOT NULL,
        feature VARCHAR(30) NULL,
        related_request_id VARCHAR(200) NULL,
        expires_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        metadata JSONB NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_wallet_tx_user_id ON wallet_transactions(user_id)",
    "CREATE INDEX IF NOT EXISTS ix_wallet_tx_user_pool ON wallet_transactions(user_id, pool)",
    "CREATE INDEX IF NOT EXISTS ix_wallet_tx_created_at ON wallet_transactions(created_at)",
]

def run_migration():
    print("Running migration: create wallet_transactions...")
    with engine.connect() as conn:
        for stmt in MIGRATION_SQL:
            stmt = stmt.strip()
            if not stmt or stmt.startswith("--"):
                continue
            try:
                conn.execute(text(stmt))
                conn.commit()
                print(f"  OK: {stmt[:70]}...")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  SKIP: {stmt[:70]}...")
                else:
                    print(f"  ERROR: {e}")
                    raise
    print("Migration complete!")

if __name__ == "__main__":
    run_migration()
