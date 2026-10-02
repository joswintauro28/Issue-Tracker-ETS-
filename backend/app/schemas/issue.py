"""Pydantic schemas for issues."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.issue import IssuePriority, IssueStatus
from app.schemas.user import UserRead


class IssueBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    priority: IssuePriority = IssuePriority.MEDIUM


class IssueCreate(IssueBase):
    assignee_id: int | None = None


class IssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    assignee_id: int | None = None


class IssueRead(IssueBase):
    id: int
    status: IssueStatus
    reporter_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime
    reporter: UserRead
    assignee: UserRead | None = None

    model_config = ConfigDict(from_attributes=True)
