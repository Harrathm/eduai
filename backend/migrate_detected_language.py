"""
Migration : ajout de la colonne detected_language à ai_chat_messages
"""
import pg8000
import sqlalchemy
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"


def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(
            text(
                "ALTER TABLE ai_chat_messages "
                "ADD COLUMN IF NOT EXISTS detected_language VARCHAR(10)"
            )
        )
        conn.commit()
        print("OK: colonne detected_language ajoutee a ai_chat_messages")


if __name__ == "__main__":
    migrate()
