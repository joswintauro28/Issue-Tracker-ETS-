"""User routes."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter()


@router.get("", response_model=list[UserRead])
def list_users(db: DbSession, current_user: CurrentUser) -> list[User]:
    """List all users (used for assignee pickers and the Users page)."""
    return db.query(User).order_by(User.name).all()
