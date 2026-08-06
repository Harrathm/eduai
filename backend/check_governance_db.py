"""Quick diagnostic: check governance columns and tables in DB."""
from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check users columns
    r = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name IN ('roles', 'active_context_role', 'is_partner')"))
    cols = [row[0] for row in r]
    print("Users governance columns:", cols if cols else "NONE FOUND")

    # Check courses columns
    r2 = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'courses' AND column_name IN ('version_number', 'is_active_version', 'category_cible', 'tag_pack_requis')"))
    cols2 = [row[0] for row in r2]
    print("Courses governance columns:", cols2 if cols2 else "NONE FOUND")

    # Check governance tables
    r3 = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('bulk_seat_vouchers', 'teacher_revenue_ledger', 'audit_impersonations')"))
    tables = [row[0] for row in r3]
    print("Governance tables:", tables if tables else "NONE FOUND")

    # Check if /catalog/courses and /catalog/stats endpoint tables are OK
    r4 = conn.execute(text("SELECT COUNT(*) FROM courses WHERE is_published = true"))
    print("Published courses:", r4.scalar())

    # Check alembic version
    r5 = conn.execute(text("SELECT version_num FROM alembic_version"))
    versions = [row[0] for row in r5]
    print("Alembic versions:", versions)
