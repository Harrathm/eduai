from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    r = conn.execute(text('SELECT is_nullable FROM information_schema.columns WHERE table_name = \'platform_settings\' AND column_name = \'school_id\'')).fetchone()
    print('Nullable:', r[0] if r else 'None')