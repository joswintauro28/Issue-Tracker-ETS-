"""Comment ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(
        ForeignKey("issues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    issue: Mapped["Issue"] = relationship(  # noqa: F821
        "Issue", back_populates="comments"
    )
    user: Mapped["User"] = relationship("User", back_populates="comments")  # noqa: F821

    @property
    def author(self) -> "User":
        """Alias for ``user`` used by the API schema (``CommentRead.author``)."""
        return self.user

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Comment id={self.id} issue_id={self.issue_id} user_id={self.user_id}>"
