"""User routes."""

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter()


@router.get("", response_model=list[UserRead])
def list_users(db: DbSession, admin: AdminUser) -> list[User]:
    """List all users. Admin only - the list exists to pick assignees, and
    only admins may assign issues."""
    return db.query(User).order_by(User.name).all()
