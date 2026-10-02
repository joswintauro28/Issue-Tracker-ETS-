"""Issue routes.

RBAC (role-based access control), enforced at the API boundary:

- **Admin**: may list *all* issues and create, edit, delete, assign and manage
  any issue.
- **Member (regular user)**: may only *view* the issues assigned to them and
  update the status of those issues (open / in_progress / closed). Members can
  never assign issues - to themselves, to the admin, or to anyone else - and
  cannot create, edit or delete issues.

Authentication (bearer token) is required for every endpoint.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.comment import Comment
from app.models.issue import Issue, IssueStatus
from app.models.user import User, UserRole
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.issue import (
    IssueAssignUpdate,
    IssueCreate,
    IssueEdit,
    IssueRead,
    IssueStatusUpdate,
    IssueUpdate,
    PaginatedIssueRead,
)

router = APIRouter()


def _get_issue_or_404(db: DbSession, issue_id: int) -> Issue:
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found.",
        )
    return issue


def _ensure_can_view(issue: Issue, user: User) -> None:
    """Admins see everything; regular users only see tasks assigned to them."""
    if user.role == UserRole.ADMIN:
        return
    if issue.assignee_id == user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this issue.",
    )


def _ensure_can_update_status(issue: Issue, user: User) -> None:
    """The admin, or the regular user the task is assigned to."""
    if user.role == UserRole.ADMIN:
        return
    if issue.assignee_id == user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only the admin or the assigned user can update this issue's status.",
    )


def _validate_assignee(db: DbSession, assignee_id: int | None) -> None:
    if assignee_id is not None and db.get(User, assignee_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Assignee with id {assignee_id} does not exist.",
        )


@router.get("", response_model=PaginatedIssueRead)
def list_issues(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1, description="1-based page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page (max 100)"),
    status_filter: IssueStatus | None = Query(default=None, alias="status"),
    assignee_id: int | None = Query(default=None, description="Filter by assignee user id"),
    unassigned: bool = Query(default=False, description="Only return unassigned issues"),
    search: str | None = Query(
        default=None,
        max_length=200,
        description="Case-insensitive search in title and description",
    ),
) -> dict[str, Any]:
    """List issues, newest first, with pagination and optional filters.

    Admins receive every issue; regular users only receive issues assigned to
    them.
    """
    query = db.query(Issue)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Issue.assignee_id == current_user.id)

    if status_filter is not None:
        query = query.filter(Issue.status == status_filter)
    if unassigned:
        query = query.filter(Issue.assignee_id.is_(None))
    elif assignee_id is not None:
        query = query.filter(Issue.assignee_id == assignee_id)
    if search is not None and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(Issue.title.ilike(term) | Issue.description.ilike(term))

    total = query.count()
    items = (
        query.order_by(Issue.created_at.desc(), Issue.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=IssueRead, status_code=status.HTTP_201_CREATED)
def create_issue(payload: IssueCreate, db: DbSession, admin: AdminUser) -> Issue:
    """Create a new issue. Admin only; the reporter and timestamps are set by the backend."""
    _validate_assignee(db, payload.assignee_id)

    issue = Issue(
        title=payload.title.strip(),
        description=payload.description,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        reporter_id=admin.id,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


@router.get("/{issue_id}", response_model=IssueRead)
def get_issue(issue_id: int, db: DbSession, current_user: CurrentUser) -> Issue:
    """Fetch a single issue (admins: any issue; members: only assigned tasks)."""
    issue = _get_issue_or_404(db, issue_id)
    _ensure_can_view(issue, current_user)
    return issue


@router.put("/{issue_id}", response_model=IssueRead)
def edit_issue(
    issue_id: int,
    payload: IssueEdit,
    db: DbSession,
    admin: AdminUser,
) -> Issue:
    """Replace an issue's editable fields. Admin only."""
    issue = _get_issue_or_404(db, issue_id)
    _validate_assignee(db, payload.assignee_id)

    issue.title = payload.title.strip()
    issue.description = payload.description
    issue.priority = payload.priority
    issue.assignee_id = payload.assignee_id
    if payload.status is not None:
        issue.status = payload.status

    db.commit()
    db.refresh(issue)
    return issue


@router.patch("/{issue_id}", response_model=IssueRead)
def update_issue(
    issue_id: int,
    payload: IssueUpdate,
    db: DbSession,
    admin: AdminUser,
) -> Issue:
    """Partially update an issue. Admin only."""
    issue = _get_issue_or_404(db, issue_id)
    data = payload.model_dump(exclude_unset=True)

    if "assignee_id" in data:
        _validate_assignee(db, data["assignee_id"])

    for field, value in data.items():
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)
    return issue


@router.patch("/{issue_id}/status", response_model=IssueRead)
def update_issue_status(
    issue_id: int,
    payload: IssueStatusUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Issue:
    """Update only the status (open / in_progress / closed).

    Allowed for admins on any issue and for regular users on issues assigned
    to them.
    """
    issue = _get_issue_or_404(db, issue_id)
    _ensure_can_update_status(issue, current_user)

    issue.status = payload.status
    db.commit()
    db.refresh(issue)
    return issue


@router.patch("/{issue_id}/assign", response_model=IssueRead)
def assign_issue(
    issue_id: int,
    payload: IssueAssignUpdate,
    db: DbSession,
    admin: AdminUser,
) -> Issue:
    """Assign the issue to a registered user, or unassign it with ``assignee_id: null``.

    Admin only: regular users can never assign tasks to themselves or anyone
    else.
    """
    issue = _get_issue_or_404(db, issue_id)
    _validate_assignee(db, payload.assignee_id)

    issue.assignee_id = payload.assignee_id
    db.commit()
    db.refresh(issue)
    return issue


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(issue_id: int, db: DbSession, admin: AdminUser) -> None:
    """Delete an issue and its comments. Admin only."""
    issue = _get_issue_or_404(db, issue_id)
    db.delete(issue)
    db.commit()


@router.get("/{issue_id}/comments", response_model=list[CommentRead])
def list_comments(issue_id: int, db: DbSession, current_user: CurrentUser) -> list[Comment]:
    """List all comments on an issue, oldest first (chronological order)."""
    issue = _get_issue_or_404(db, issue_id)
    _ensure_can_view(issue, current_user)
    # Explicit ordering (with id as tiebreaker) so chronological order is
    # guaranteed even when several comments share the same timestamp.
    comments = (
        db.query(Comment)
        .filter(Comment.issue_id == issue.id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .all()
    )
    return comments


@router.post(
    "/{issue_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED
)
def create_comment(
    issue_id: int,
    payload: CommentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Comment:
    """Add a comment to an issue on behalf of the current user.

    Admins can comment on any issue; regular users only on issues assigned to
    them.
    """
    issue = _get_issue_or_404(db, issue_id)
    _ensure_can_view(issue, current_user)

    comment = Comment(
        issue_id=issue.id,
        user_id=current_user.id,
        content=payload.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
