"""
Migration: Création des tables ai_conversations et ai_chat_messages
pour l'historique des conversations avec l'assistant IA.

Exécuter: python migrate_conversations.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.db import engine


def migrate():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL DEFAULT 'Nouvelle conversation',
                subject VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ai_conv_user_id ON ai_conversations(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ai_conv_updated_at ON ai_conversations(updated_at)"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_chat_messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ai_msg_conv_id ON ai_chat_messages(conversation_id)"))

    print("Migration terminée: ai_conversations + ai_chat_messages créées.")


if __name__ == "__main__":
    migrate()
