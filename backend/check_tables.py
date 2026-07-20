import sys
sys.path.insert(0, ".")
from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    for table in ["content_forum_threads", "content_forum_replies", "content_media_assets", "content_chapters", "content_lessons"]:
        result = conn.execute(text(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='{table}' ORDER BY ordinal_position"))
        print(f"\n=== {table} ===")
        for row in result:
            print(f"  {row[0]}: {row[1]} {'NULL' if row[2]=='YES' else 'NOT NULL'}")
