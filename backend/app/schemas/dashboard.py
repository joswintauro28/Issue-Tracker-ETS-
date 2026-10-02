"""Pydantic schemas for the dashboard."""

from pydantic import BaseModel

from app.schemas.issue import IssueRead


class DashboardSummaryRead(BaseModel):
    """Aggregated counters and lists for the dashboard.

    All values are computed from the database at request time - nothing is
    cached or mocked.
    """

    total_issues: int
    open_issues: int
    in_progress_issues: int
    closed_issues: int
    recent_issues: list[IssueRead]
    my_assigned_issues: list[IssueRead]
