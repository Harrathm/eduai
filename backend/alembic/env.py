"""
Alembic environment configuration for EDUAI Learning.

Reads DATABASE_URL from the environment (or .env) and runs migrations
against the same PostgreSQL database used by the application.
"""
import os
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ---------------------------------------------------------------------------
# Load .env file if present (same directory as alembic.ini)
# ---------------------------------------------------------------------------
_backend_root = Path(__file__).resolve().parent.parent
_dotenv = _backend_root / ".env"
if _dotenv.exists():
    for line in _dotenv.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

# Ensure the backend package is importable
sys.path.insert(0, str(_backend_root))

# ---------------------------------------------------------------------------
# Alembic Config object
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Override sqlalchemy.url from DATABASE_URL env var
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
else:
    raise RuntimeError(
        "DATABASE_URL must be set in the environment or in .env "
        "before running Alembic migrations."
    )

# ---------------------------------------------------------------------------
# Import ALL models so Alembic can autodetect them via Base.metadata
# ---------------------------------------------------------------------------
# 1) Platform models (Base) — School, User, Course, Module, Lesson, …
from app.models import Base  # noqa: E402

# 2) LMS models (LmsBase) — but LmsBase uses a DIFFERENT metadata, so we
#    need to merge it into Base.metadata.  The models_lms module creates its
#    own DeclarativeBase.  We re-bind those tables to our Base by importing
#    after Base exists.  See the import below.
import app.models_lms  # noqa: E402, F401  — registers LmsBase tables

# 3) AI conversation models — uses app.models.Base directly, just import.
import app.models_ai_conversations  # noqa: E402, F401

# ---------------------------------------------------------------------------
# Merge LmsBase metadata into the main Base metadata so Alembic sees all tables.
# ---------------------------------------------------------------------------
from sqlalchemy import MetaData  # noqa: E402

def _merge_metadata(source: MetaData, target: MetaData) -> None:
    """Copy all tables from *source* into *target* metadata in-place."""
    for table in source.tables.values():
        table.tometadata(target)

# Import LmsBase from models_lms
from app.models_lms import LmsBase  # noqa: E402

_merge_metadata(LmsBase.metadata, Base.metadata)

# After the merge, Base.metadata.reflect() (called by Alembic) will contain
# every table from both Base and LmsBase.

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode (generates SQL without a live connection)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Generate SQL script without a database connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode (runs migrations against a live database)
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    """Run migrations against a live database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
