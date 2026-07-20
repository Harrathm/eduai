#!/bin/bash

set -e

echo "Starting EDUAI Backend..."

echo "Checking database connection..."
python -c "from app.db import engine; engine.connect()" 2>/dev/null || {
    echo "Database not ready, waiting..."
    sleep 5
}

echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} $@