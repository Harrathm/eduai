"""Apply governance migration SQL directly to the database."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+pg8000://postgres:gill4264@localhost:5432/eduai"

from sqlalchemy import text
from app.db.session import engine

STATEMENTS = [
    # 1. Users columns
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS roles JSONB NOT NULL DEFAULT '[]'::jsonb",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS active_context_role VARCHAR(30)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_partner BOOLEAN NOT NULL DEFAULT FALSE",

    # 2. Courses columns
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1",
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS is_active_version BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS category_cible VARCHAR(30) NOT NULL DEFAULT 'Scolaire'",
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS tag_pack_requis VARCHAR(20) NOT NULL DEFAULT 'Basic'",

    # 3. Bulk seats table
    """CREATE TABLE IF NOT EXISTS bulk_seat_vouchers (
        id SERIAL PRIMARY KEY,
        school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
        formation_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        code VARCHAR(50) NOT NULL UNIQUE,
        status VARCHAR(20) NOT NULL DEFAULT 'unused',
        consumed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    )""",
    "CREATE INDEX IF NOT EXISTS ix_bulk_seat_vouchers_school ON bulk_seat_vouchers(school_id)",
    "CREATE INDEX IF NOT EXISTS ix_bulk_seat_vouchers_formation ON bulk_seat_vouchers(formation_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_bulk_seat_vouchers_code ON bulk_seat_vouchers(code)",

    # 4. Revenue ledger table
    """CREATE TABLE IF NOT EXISTS teacher_revenue_ledger (
        id SERIAL PRIMARY KEY,
        teacher_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        lesson_id INTEGER REFERENCES lessons(id) ON DELETE SET NULL,
        consumption_count INTEGER NOT NULL DEFAULT 0,
        revenue_amount NUMERIC(10,2) NOT NULL DEFAULT 0.00,
        period_month DATE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    )""",
    "CREATE INDEX IF NOT EXISTS ix_teacher_revenue_ledger_teacher ON teacher_revenue_ledger(teacher_id)",
    "CREATE INDEX IF NOT EXISTS ix_teacher_revenue_ledger_lesson ON teacher_revenue_ledger(lesson_id)",
    "CREATE INDEX IF NOT EXISTS ix_teacher_revenue_ledger_period ON teacher_revenue_ledger(period_month)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_teacher_lesson_period ON teacher_revenue_ledger(teacher_id, lesson_id, period_month)",

    # 5. Audit impersonations table
    """CREATE TABLE IF NOT EXISTS audit_impersonations (
        id SERIAL PRIMARY KEY,
        impersonator_id INTEGER NOT NULL REFERENCES users.id ON DELETE CASCADE,
        target_user_id INTEGER NOT NULL REFERENCES users.id ON DELETE CASCADE,
        reason TEXT NOT NULL DEFAULT '',
        started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        ended_at TIMESTAMP WITH TIME ZONE,
        session_duration_seconds INTEGER,
        ip_address VARCHAR(45)
    )""",
    "CREATE INDEX IF NOT EXISTS ix_audit_imp_impersonator ON audit_impersonations(impersonator_id)",
    "CREATE INDEX IF NOT EXISTS ix_audit_imp_target ON audit_impersonations(target_user_id)",

    # 6. Backward compat
    "UPDATE users SET roles = json_build_array(role)::jsonb WHERE roles = '[]'::jsonb",
]

def apply():
    with engine.connect() as conn:
        for i, stmt in enumerate(STATEMENTS):
            try:
                conn.execute(text(stmt))
                conn.commit()
                print(f"  [{i+1}/{len(STATEMENTS)}] OK: {stmt.strip()[:70]}...")
            except Exception as e:
                conn.rollback()
                err_msg = str(e)[:120]
                print(f"  [{i+1}/{len(STATEMENTS)}] SKIP: {stmt.strip()[:50]}... -> {err_msg}")
    print("\nMigration applied.")

if __name__ == "__main__":
    apply()
