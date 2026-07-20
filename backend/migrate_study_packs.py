"""
Migration: Ajout des study_packs, pack_purchases et niveau_scolaire
"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"
)

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # 1. Ajouter niveau_scolaire à users
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN niveau_scolaire VARCHAR(50)"))
            print("OK: users.niveau_scolaire added")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("SKIP: users.niveau_scolaire already exists")
            else:
                raise

        # 2. Ajouter niveau_scolaire à courses
        try:
            conn.execute(text("ALTER TABLE courses ADD COLUMN niveau_scolaire VARCHAR(50)"))
            print("OK: courses.niveau_scolaire added")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("SKIP: courses.niveau_scolaire already exists")
            else:
                raise

        # 3. Créer la table study_packs
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS study_packs (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                niveau_scolaire VARCHAR(50) NOT NULL,
                matieres JSON,
                price FLOAT NOT NULL,
                currency VARCHAR(10) DEFAULT 'TND',
                validity_duration_days INTEGER DEFAULT 365,
                status VARCHAR(20) DEFAULT 'draft',
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("OK: study_packs table created")

        # 4. Index study_packs
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_study_packs_niveau ON study_packs(niveau_scolaire)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_study_packs_status ON study_packs(status)"))
        print("OK: study_packs indexes created")

        # 5. Créer la table pack_purchases
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pack_purchases (
                id SERIAL PRIMARY KEY,
                pack_id INTEGER NOT NULL REFERENCES study_packs(id) ON DELETE CASCADE,
                purchaser_type VARCHAR(20) NOT NULL,
                student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
                valid_from TIMESTAMP NOT NULL,
                valid_until TIMESTAMP NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                amount_paid FLOAT NOT NULL,
                currency VARCHAR(10) DEFAULT 'TND',
                transaction_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("OK: pack_purchases table created")

        # 6. Index pack_purchases
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pack_purchases_pack_id ON pack_purchases(pack_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pack_purchases_student_id ON pack_purchases(student_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pack_purchases_school_id ON pack_purchases(school_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pack_purchases_status ON pack_purchases(status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pack_purchases_valid_until ON pack_purchases(valid_until)"))
        print("OK: pack_purchases indexes created")

        conn.commit()
        print("\nMigration completed successfully!")


if __name__ == "__main__":
    migrate()
