"""Seed the database.

Usage (run from the ``backend`` directory):

    .venv/Scripts/python seed.py            # ensure the Admin exists (idempotent)
    .venv/bin/python seed.py                # same on macOS / Linux
    python seed.py --demo                   # additionally seed local demo data

The Admin account is configured entirely through environment variables (or
``backend/.env``):

    ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD

Behaviour:
- Creates the Admin with the ``admin`` role ONLY if no user with that email
  exists yet; the password is hashed with bcrypt and never printed.
- If the email already exists, the script does nothing to that row's identity
  and only ensures the role is ``admin`` (logged).
- If ADMIN_EMAIL/ADMIN_PASSWORD are not configured, seeding is skipped with a
  warning (exit code 0) - so the script is safe to run in production.
- Runs are idempotent: running it any number of times never duplicates data.
- ``--demo`` additionally creates local demo users and issues; never use it in
  production.
"""

import argparse
import sys

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.issue import Issue, IssuePriority, IssueStatus
from app.models.user import User, UserRole

DEMO_PASSWORD = "password123"  # demo-only credentials for --demo, never for the admin
MIN_ADMIN_PASSWORD_LENGTH = 8


def seed_admin(db: Session) -> User | None:
    """Create (or verify) the admin account from configuration. Idempotent."""
    email = settings.ADMIN_EMAIL.strip().lower() if settings.ADMIN_EMAIL else ""
    password = settings.ADMIN_PASSWORD or ""
    name = settings.ADMIN_NAME.strip() if settings.ADMIN_NAME else ""

    if not email and not password:
        print("Admin seeding skipped: ADMIN_EMAIL / ADMIN_PASSWORD are not configured.")
        return None
    if not email or not password:
        print(
            "Admin seeding skipped: both ADMIN_EMAIL and ADMIN_PASSWORD must be set.",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        print(
            "Admin seeding failed: ADMIN_PASSWORD must be at least "
            f"{MIN_ADMIN_PASSWORD_LENGTH} characters.",
            file=sys.stderr,
        )
        sys.exit(1)

    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        if existing.role != UserRole.ADMIN:
            existing.role = UserRole.ADMIN
            db.commit()
            print(f"Admin user {email} already existed - role ensured to 'admin'.")
        else:
            print(f"Admin user {email} already exists - nothing to do.")
        return existing

    admin = User(
        name=name or "Admin",
        email=email,
        hashed_password=hash_password(password),
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print(f"Created admin user {email} (id={admin.id}).")
    return admin


def seed_demo(db: Session, admin: User | None) -> None:
    """Create local demo users and issues. Skipped when data already exists."""
    if db.query(User).filter(User.email == "alice@example.com").first() is not None:
        print("Demo data already present - skipping demo seed.")
        return

    users = {
        "alice": User(
            name="Alice Nguyen",
            email="alice@example.com",
            hashed_password=hash_password(DEMO_PASSWORD),
            role=UserRole.USER,
        ),
        "bob": User(
            name="Bob Martinez",
            email="bob@example.com",
            hashed_password=hash_password(DEMO_PASSWORD),
            role=UserRole.USER,
        ),
    }
    db.add_all(users.values())
    db.commit()

    reporter_id = admin.id if admin is not None else None

    issues = [
        Issue(
            title="Login page shows stale error message",
            description="After a failed login the error message stays visible after navigating back.",
            status=IssueStatus.OPEN,
            priority=IssuePriority.MEDIUM,
            reporter_id=reporter_id or users["alice"].id,
            assignee_id=users["alice"].id,
        ),
        Issue(
            title="Slow dashboard query",
            description="Dashboard aggregates take >2s with 10k issues. Consider caching counts.",
            status=IssueStatus.IN_PROGRESS,
            priority=IssuePriority.HIGH,
            reporter_id=users["alice"].id,
            assignee_id=users["bob"].id,
        ),
        Issue(
            title="Add favicon and page title",
            description="Browser tab shows the default Vite icon.",
            status=IssueStatus.CLOSED,
            priority=IssuePriority.LOW,
            reporter_id=users["bob"].id,
            assignee_id=reporter_id,
        ),
    ]
    db.add_all(issues)
    db.commit()
    print("Seeded demo users alice@example.com / bob@example.com and 3 issues.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the database (idempotent).")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Also seed local demo users and issues (never in production).",
    )
    args = parser.parse_args()

    init_db()

    db = SessionLocal()
    try:
        admin = seed_admin(db)
        if args.demo:
            seed_demo(db, admin)
    finally:
        db.close()


if __name__ == "__main__":
    main()
