"""Database initialization helper.

SQLite keeps local development zero-config: any missing tables are created on
startup. For PostgreSQL deployments, prefer Alembic migrations instead of
relying on ``create_all`` for schema evolution.

Also performs one tiny, idempotent data normalization: rows still carrying the
legacy ``MEMBER`` role are upgraded to ``USER`` (the role was renamed), so
existing databases keep working on both SQLite and PostgreSQL.

Note: SQLAlchemy persists enum member *names* (``ADMIN``/``USER``), not their
values - the update below intentionally matches the stored names.
"""

from sqlalchemy import text

from app import models  # noqa: F401  (register models on Base.metadata)
from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    """Create any missing tables and normalize legacy role values."""
    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE users SET role = 'USER' WHERE role = 'MEMBER'")
        )
