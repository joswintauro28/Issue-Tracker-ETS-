"""Dashboard routes."""

from typing import Any

from fastapi import APIRouter
from sqlalchemy import func

from app.api.deps import CurrentUser, DbSession
from app.models.issue import Issue, IssueStatus
from app.models.user import UserRole
from app.schemas.dashboard import DashboardSummaryRead

router = APIRouter()

RECENT_ISSUES_LIMIT = 5
MY_ASSIGNED_LIMIT = 5


@router.get("/summary", response_model=DashboardSummaryRead)
def dashboard_summary(db: DbSession, current_user: CurrentUser) -> dict[str, Any]:
    """Real-time dashboard counters and lists, computed from the database.

    - Admins see the whole project; regular users see only tasks assigned to
      them (RBAC scope is applied to every query below).
    - Counts per status come from a single ``GROUP BY`` query.
    - ``recent_issues`` are the newest issues within the caller's scope.
    - ``my_assigned_issues`` are the caller's assigned issues that are not
      closed (i.e. still actionable), ordered by last update.
    """
    scoped = db.query(Issue)
    if current_user.role != UserRole.ADMIN:
        scoped = scoped.filter(Issue.assignee_id == current_user.id)

    total_issues = scoped.count()

    status_rows = (
        scoped.with_entities(Issue.status, func.count(Issue.id)).group_by(Issue.status).all()
    )
    counts: dict[IssueStatus, int] = {status_value: 0 for status_value in IssueStatus}
    for status_value, count in status_rows:
        counts[status_value] = count

    recent_issues = (
        scoped.order_by(Issue.created_at.desc(), Issue.id.desc())
        .limit(RECENT_ISSUES_LIMIT)
        .all()
    )

    my_assigned_issues = (
        db.query(Issue)
        .filter(Issue.assignee_id == current_user.id)
        .filter(Issue.status != IssueStatus.CLOSED)
        .order_by(Issue.updated_at.desc(), Issue.id.desc())
        .limit(MY_ASSIGNED_LIMIT)
        .all()
    )

    return {
        "total_issues": total_issues,
        "open_issues": counts[IssueStatus.OPEN],
        "in_progress_issues": counts[IssueStatus.IN_PROGRESS],
        "closed_issues": counts[IssueStatus.CLOSED],
        "recent_issues": recent_issues,
        "my_assigned_issues": my_assigned_issues,
    }
