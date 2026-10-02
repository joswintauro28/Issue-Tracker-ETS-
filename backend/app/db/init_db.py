"""Database initialization helper.

SQLite keeps local development zero-config: any missing tables are created on
startup. For PostgreSQL deployments, prefer Alembic migrations instead of
relying on ``create_all`` for schema evolution.
"""

from app import models  # noqa: F401  (register models on Base.metadata)
from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    """Create any missing tables on the configured database."""
    Base.metadata.create_all(bind=engine)
