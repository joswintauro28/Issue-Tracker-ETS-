"""Pytest configuration.

All tests run against a dedicated SQLite database so the development database
is never touched. The DATABASE_URL environment variable must be set BEFORE any
``app`` import because settings are loaded once at import time.
"""

import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_issue_tracker.db"

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app

TEST_DB_FILE = Path("test_issue_tracker.db")


@pytest.fixture(scope="session")
def client():
    """HTTP client bound to the app, with a fresh database for the test run."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()
