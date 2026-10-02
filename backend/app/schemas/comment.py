"""Pydantic schemas for comments."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import UserRead


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Comment content cannot be blank.")
        return stripped


class CommentRead(BaseModel):
    id: int
    issue_id: int
    user_id: int
    content: str
    created_at: datetime
    author: UserRead

    model_config = ConfigDict(from_attributes=True)
