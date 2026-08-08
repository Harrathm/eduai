#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
python -c "
import time, os, sys
from sqlalchemy import create_engine, text
url = os.environ.get('DATABASE_URL', '')
if url:
    for i in range(30):
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            print('Database ready!')
            sys.exit(0)
        except Exception:
            time.sleep(2)
    print('Database not ready after 60s, exiting')
    sys.exit(1)
else:
    print('No DATABASE_URL set, skipping wait')
"

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-2} --log-level ${LOG_LEVEL:-info}
