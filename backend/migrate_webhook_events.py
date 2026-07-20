"""
Migration: Créer la table webhook_events pour l'idempotence des webhooks Stripe.
"""

from sqlalchemy import text
from app.db import engine


def migrate():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS webhook_events (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(255) UNIQUE NOT NULL,
                event_type VARCHAR(100),
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_webhook_events_event_id ON webhook_events(event_id)"))
        conn.commit()
        print("Table webhook_events created successfully")


if __name__ == "__main__":
    migrate()
