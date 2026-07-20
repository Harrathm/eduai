"""Shared DB connection helper for scripts and utilities."""
import os
import pg8000


def get_connection(database: str = "eduai"):
    """Return a pg8000 connection using environment variables.

    Reads DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, or parses DATABASE_URL.
    """
    url = os.environ.get("DATABASE_URL", "")
    if url:
        # Parse postgresql+pg8000://user:password@host:port/dbname
        from urllib.parse import urlparse
        parsed = urlparse(url.replace("+pg8000", ""))
        user = parsed.username or "postgres"
        password = parsed.password or ""
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 5432
        dbname = parsed.path.lstrip("/") or database
    else:
        user = os.environ.get("DB_USER", "postgres")
        password = os.environ.get("DB_PASSWORD", "")
        host = os.environ.get("DB_HOST", "127.0.0.1")
        port = int(os.environ.get("DB_PORT", "5432"))
        dbname = database

    return pg8000.connect(user=user, password=password, host=host, port=port, database=dbname)
