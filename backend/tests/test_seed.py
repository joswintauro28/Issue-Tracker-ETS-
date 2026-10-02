"""Tests for the admin seed script (backend/seed.py).

The real script is executed as a subprocess so environment handling, hashing
and idempotency are verified end-to-end. The subprocess inherits DATABASE_URL
from the test session, so it seeds the isolated test database.
"""

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

from app.core.security import verify_password
from app.db.session import SessionLocal, engine
from app.models.user import User, UserRole

BACKEND_DIR = Path(__file__).resolve().parent.parent

ADMIN_ENV = {
    "ADMIN_NAME": "Seed Admin",
    "ADMIN_EMAIL": "seed.admin@example.com",
    "ADMIN_PASSWORD": "seed-secret-123",
}


def run_seed(env_overrides: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    """Run seed.py with explicit ADMIN_* vars so the local .env cannot leak in."""
    env = {
        **os.environ,
        "ADMIN_NAME": "",
        "ADMIN_EMAIL": "",
        "ADMIN_PASSWORD": "",
        **env_overrides,
    }
    return subprocess.run(
        [sys.executable, "seed.py", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _get_user(email: str) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


def test_seed_creates_admin_and_is_idempotent(client):
    first = run_seed(ADMIN_ENV)
    assert first.returncode == 0, first.stderr
    assert "Created admin user" in first.stdout
    # The password must never be printed.
    assert ADMIN_ENV["ADMIN_PASSWORD"] not in first.stdout + first.stderr

    admin = _get_user(ADMIN_ENV["ADMIN_EMAIL"])
    assert admin is not None
    assert admin.role == UserRole.ADMIN
    assert admin.name == "Seed Admin"
    assert admin.hashed_password != ADMIN_ENV["ADMIN_PASSWORD"]
    assert verify_password(ADMIN_ENV["ADMIN_PASSWORD"], admin.hashed_password)
    first_id = admin.id

    # Second run: no new user, no error (idempotent).
    second = run_seed(ADMIN_ENV)
    assert second.returncode == 0, second.stderr
    assert "already exists" in second.stdout

    db = SessionLocal()
    try:
        count = db.query(User).filter(User.email == ADMIN_ENV["ADMIN_EMAIL"]).count()
    finally:
        db.close()
    assert count == 1
    assert _get_user(ADMIN_ENV["ADMIN_EMAIL"]).id == first_id


def test_seed_promotes_existing_regular_user(client):
    """If the configured admin email already registered as a regular user, the
    seed only ensures the admin role (it never duplicates the account)."""
    promote_email = "promoted.admin@example.com"
    promote_env = {**ADMIN_ENV, "ADMIN_EMAIL": promote_email}

    # Register via the API first (role=user).
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Future Admin",
            "email": promote_email,
            "password": "seed-secret-123",
            "confirm_password": "seed-secret-123",
        },
    )
    assert response.status_code == 201, response.text
    assert _get_user(promote_email).role == UserRole.USER

    result = run_seed(promote_env)
    assert result.returncode == 0, result.stderr
    assert "role ensured" in result.stdout

    user = _get_user(promote_email)
    assert user is not None
    assert user.role == UserRole.ADMIN
    # Identity untouched: same name, same account.
    assert user.name == "Future Admin"

    db = SessionLocal()
    try:
        count = db.query(User).filter(User.email == promote_email).count()
    finally:
        db.close()
    assert count == 1


def test_seed_skips_without_configuration(client):
    result = run_seed({})
    assert result.returncode == 0, result.stderr
    assert "skipped" in result.stdout.lower()


def test_seed_rejects_weak_password(client):
    weak_env = {**ADMIN_ENV, "ADMIN_EMAIL": "weak.admin@example.com", "ADMIN_PASSWORD": "short"}
    result = run_seed(weak_env)
    assert result.returncode != 0
    assert "at least" in result.stderr
    # No weak-password account was created.
    assert _get_user("weak.admin@example.com") is None


def test_seed_requires_password_when_email_set(client):
    """Both variables must be set together."""
    result = run_seed({"ADMIN_EMAIL": "someone@example.com"})
    assert result.returncode != 0


def test_seed_normalizes_legacy_member_role(client):
    """Rows created before the role rename (MEMBER) are migrated to USER.
    SQLAlchemy persists enum member names, so the legacy row stores 'MEMBER'."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (name, email, hashed_password, role) "
                "VALUES ('Legacy User', 'legacy@example.com', 'x', 'MEMBER')"
            )
        )

    result = run_seed(ADMIN_ENV)
    assert result.returncode == 0, result.stderr

    legacy = _get_user("legacy@example.com")
    assert legacy is not None
    assert legacy.role == UserRole.USER
