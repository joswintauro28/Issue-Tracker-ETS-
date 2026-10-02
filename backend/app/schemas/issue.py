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


class IssueEdit(BaseModel):
    """Full replacement of an issue's editable fields (PUT semantics)."""

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    priority: IssuePriority = IssuePriority.MEDIUM
    status: IssueStatus | None = None
    assignee_id: int | None = None


class IssueUpdate(BaseModel):
    """Partial update: only the provided fields are changed."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    assignee_id: int | None = None


class IssueStatusUpdate(BaseModel):
    status: IssueStatus


class IssueAssignUpdate(BaseModel):
    assignee_id: int | None = Field(
        default=None,
        description="Registered user id to assign the issue to, or null to unassign.",
    )


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


class PaginatedIssueRead(BaseModel):
    """Page of issues plus the metadata needed to render pagination controls."""

    items: list[IssueRead]
    total: int
    page: int
    page_size: int
