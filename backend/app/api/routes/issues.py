"""Issue routes."""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models.comment import Comment
from app.models.issue import Issue, IssueStatus
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.issue import IssueCreate, IssueRead, IssueUpdate

router = APIRouter()


def _get_issue_or_404(db: DbSession, issue_id: int) -> Issue:
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found.",
        )
    return issue


def _validate_assignee(db: DbSession, assignee_id: int | None) -> None:
    if assignee_id is not None and db.get(User, assignee_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Assignee with id {assignee_id} does not exist.",
        )


@router.get("", response_model=list[IssueRead])
def list_issues(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: IssueStatus | None = Query(default=None, alias="status"),
) -> list[Issue]:
    """List issues, newest first, optionally filtered by status."""
    query = db.query(Issue).order_by(Issue.created_at.desc())
    if status_filter is not None:
        query = query.filter(Issue.status == status_filter)
    return query.all()


@router.post("", response_model=IssueRead, status_code=status.HTTP_201_CREATED)
def create_issue(payload: IssueCreate, db: DbSession, current_user: CurrentUser) -> Issue:
    """Create a new issue reported by the current user."""
    _validate_assignee(db, payload.assignee_id)

    issue = Issue(
        title=payload.title.strip(),
        description=payload.description,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        reporter_id=current_user.id,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


@router.get("/{issue_id}", response_model=IssueRead)
def get_issue(issue_id: int, db: DbSession, current_user: CurrentUser) -> Issue:
    """Fetch a single issue by id."""
    return _get_issue_or_404(db, issue_id)


@router.patch("/{issue_id}", response_model=IssueRead)
def update_issue(
    issue_id: int,
    payload: IssueUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Issue:
    """Partially update an issue (title, description, status, priority, assignee)."""
    issue = _get_issue_or_404(db, issue_id)
    data = payload.model_dump(exclude_unset=True)

    if "assignee_id" in data:
        _validate_assignee(db, data["assignee_id"])

    for field, value in data.items():
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)
    return issue


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(issue_id: int, db: DbSession, current_user: CurrentUser) -> None:
    """Delete an issue."""
    issue = _get_issue_or_404(db, issue_id)
    db.delete(issue)
    db.commit()


@router.get("/{issue_id}/comments", response_model=list[CommentRead])
def list_comments(issue_id: int, db: DbSession, current_user: CurrentUser) -> list[Comment]:
    """List all comments on an issue, oldest first."""
    issue = _get_issue_or_404(db, issue_id)
    return list(issue.comments)


@router.post(
    "/{issue_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED
)
def create_comment(
    issue_id: int,
    payload: CommentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Comment:
    """Add a comment to an issue on behalf of the current user."""
    issue = _get_issue_or_404(db, issue_id)

    comment = Comment(
        issue_id=issue.id,
        user_id=current_user.id,
        content=payload.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
