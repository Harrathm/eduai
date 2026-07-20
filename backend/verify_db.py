import os
os.environ['DATABASE_URL'] = 'postgresql+pg8000://postgres:gill4264@localhost:5432/eduai'
from sqlalchemy import create_engine, text
e = create_engine(os.environ['DATABASE_URL'])
with e.connect() as c:
    tables = c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")).fetchall()
    print(f"Tables: {len(tables)}")
    for row in tables:
        tn = row[0]
        cnt = c.execute(text(f'SELECT count(*) FROM "{tn}"')).scalar()
        if cnt > 0:
            print(f"  {tn}: {cnt} rows")
    c.close()
