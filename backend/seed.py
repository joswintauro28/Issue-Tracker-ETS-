"""Seed the database with demo users and issues.

Run from the ``backend`` directory:
    .venv/Scripts/python seed.py        (Windows)
    .venv/bin/python seed.py            (macOS / Linux)

Demo accounts (password: ``password123``):
    admin@example.com  (admin)
    alice@example.com  (member)
    bob@example.com    (member)
"""

from app import models  # noqa: F401  (register models on Base.metadata)
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.issue import Issue, IssuePriority, IssueStatus
from app.models.user import User, UserRole

DEMO_PASSWORD = "password123"


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).first() is not None:
            print("Database already contains data - skipping seed.")
            return

        users = {
            "admin": User(
                name="Admin",
                email="admin@example.com",
                hashed_password=hash_password(DEMO_PASSWORD),
                role=UserRole.ADMIN,
            ),
            "alice": User(
                name="Alice Nguyen",
                email="alice@example.com",
                hashed_password=hash_password(DEMO_PASSWORD),
                role=UserRole.MEMBER,
            ),
            "bob": User(
                name="Bob Martinez",
                email="bob@example.com",
                hashed_password=hash_password(DEMO_PASSWORD),
                role=UserRole.MEMBER,
            ),
        }
        db.add_all(users.values())
        db.commit()

        db.add_all(
            [
                Issue(
                    title="Login page shows stale error message",
                    description="After a failed login the error message stays visible after navigating back.",
                    status=IssueStatus.OPEN,
                    priority=IssuePriority.MEDIUM,
                    reporter_id=users["admin"].id,
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
                    assignee_id=users["admin"].id,
                ),
            ]
        )
        db.commit()
        print("Seed complete. Login with admin@example.com / password123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
