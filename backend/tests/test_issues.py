"""Tests for issue management: creation, editing, assignment, status changes,
authorization rules, filtering, search and pagination.

RBAC model under test: admins create/edit/delete/assign and see everything;
regular members only view their assigned tasks and update their status.
"""

import pytest

from app.db.session import SessionLocal
from app.models.comment import Comment
from app.models.user import User, UserRole

ISSUES_URL = "/api/issues"
USERS_URL = "/api/users"
PASSWORD = "supersecret123"

USERS = {
    "reporter": {"name": "Rita Reporter", "email": "rita@example.com"},
    "assignee": {"name": "Andy Assignee", "email": "andy@example.com"},
    "outsider": {"name": "Ollie Outsider", "email": "ollie@example.com"},
    "admin": {"name": "Ada Admin", "email": "ada-admin@example.com"},
}


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def tokens(client):
    """Register the fixture users and return {key: access_token}."""
    result = {}
    for key, payload in USERS.items():
        response = client.post(
            "/api/auth/register",
            json={**payload, "password": PASSWORD, "confirm_password": PASSWORD},
        )
        assert response.status_code == 201, response.text
        login = client.post(
            "/api/auth/login", json={"email": payload["email"], "password": PASSWORD}
        )
        assert login.status_code == 200, login.text
        result[key] = login.json()["access_token"]

    # Promote the admin directly in the database: there is intentionally no
    # public endpoint that changes roles.
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == USERS["admin"]["email"]).first()
        assert admin is not None
        admin.role = UserRole.ADMIN
        db.commit()
    finally:
        db.close()
    return result


@pytest.fixture(scope="module")
def user_ids(client, tokens):
    users = client.get(USERS_URL, headers=auth(tokens["admin"])).json()
    return {
        key: next(user["id"] for user in users if user["email"] == payload["email"])
        for key, payload in USERS.items()
    }


@pytest.fixture(scope="module")
def base_issues(client, tokens, user_ids):
    """Three issues created by the admin: assigned, plain open, and closed."""
    creator = tokens["admin"]

    assigned = client.post(
        ISSUES_URL,
        json={
            "title": "Base issue assigned",
            "description": "Assigned to Andy",
            "priority": "high",
            "assignee_id": user_ids["assignee"],
        },
        headers=auth(creator),
    )
    assert assigned.status_code == 201, assigned.text

    opened = client.post(
        ISSUES_URL,
        json={"title": "Base issue open", "description": "Plain open issue"},
        headers=auth(creator),
    )
    assert opened.status_code == 201, opened.text

    closed = client.post(
        ISSUES_URL,
        json={"title": "Base issue closed", "description": "Closed issue"},
        headers=auth(creator),
    )
    assert closed.status_code == 201, closed.text
    marked = client.patch(
        f"{ISSUES_URL}/{closed.json()['id']}/status",
        json={"status": "closed"},
        headers=auth(creator),
    )
    assert marked.status_code == 200, marked.text

    return {
        "assigned": assigned.json(),
        "open": opened.json(),
        "closed": marked.json(),
    }


# --- Creation (admin only) ------------------------------------------------------


def test_create_issue_requires_authentication(client):
    assert (
        client.post(ISSUES_URL, json={"title": "Anonymous issue", "priority": "low"}).status_code
        == 401
    )


def test_create_issue_rejected_for_members(client, tokens):
    response = client.post(
        ISSUES_URL,
        json={"title": "Member tried to create", "priority": "low"},
        headers=auth(tokens["reporter"]),
    )
    assert response.status_code == 403
    assert "administrators" in response.json()["detail"]


def test_create_issue_records_reporter_and_timestamps(client, tokens, base_issues):
    created = client.post(
        ISSUES_URL,
        json={"title": "Reporter check issue", "description": "Who filed this?"},
        headers=auth(tokens["admin"]),
    )
    assert created.status_code == 201
    body = created.json()
    assert body["reporter"]["email"] == USERS["admin"]["email"]
    assert body["reporter_id"] == body["reporter"]["id"]
    assert body["status"] == "open"
    assert body["priority"] == "medium"
    assert body["assignee"] is None
    assert body["created_at"]
    assert body["updated_at"]


def test_create_issue_rejects_invalid_fields(client, tokens):
    headers = auth(tokens["admin"])
    assert (
        client.post(ISSUES_URL, json={"title": "ab", "priority": "low"}, headers=headers).status_code
        == 422
    )  # title too short
    assert (
        client.post(
            ISSUES_URL,
            json={"title": "Valid title here", "priority": "urgent"},
            headers=headers,
        ).status_code
        == 422
    )  # invalid priority value
    assert client.post(ISSUES_URL, json={}, headers=headers).status_code == 422


def test_create_issue_rejects_nonexistent_assignee(client, tokens):
    response = client.post(
        ISSUES_URL,
        json={"title": "Bad assignee issue", "assignee_id": 999999},
        headers=auth(tokens["admin"]),
    )
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]


# --- Retrieval ------------------------------------------------------------------


def test_get_issue_details(client, tokens, user_ids, base_issues):
    # The assignee may view the task...
    assignee_view = client.get(
        f"{ISSUES_URL}/{base_issues['assigned']['id']}", headers=auth(tokens["assignee"])
    )
    assert assignee_view.status_code == 200

    # ...and the admin may view any issue.
    response = client.get(
        f"{ISSUES_URL}/{base_issues['assigned']['id']}", headers=auth(tokens["admin"])
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Base issue assigned"
    assert body["reporter"]["email"] == USERS["admin"]["email"]
    assert body["assignee"]["id"] == user_ids["assignee"]
    assert body["created_at"] and body["updated_at"]


def test_get_missing_issue_returns_404(client, tokens):
    response = client.get(f"{ISSUES_URL}/999999", headers=auth(tokens["admin"]))
    assert response.status_code == 404
    assert response.json()["detail"] == "Issue not found."


def test_member_cannot_view_unassigned_issue(client, tokens, base_issues):
    response = client.get(
        f"{ISSUES_URL}/{base_issues['open']['id']}", headers=auth(tokens["reporter"])
    )
    assert response.status_code == 403
    assert "do not have access" in response.json()["detail"]


# --- Editing: admin only ----------------------------------------------------------


def test_edit_issue_by_member_reporter_forbidden(client, tokens, base_issues):
    """RBAC: regular users cannot edit issues, even ones they can see."""
    response = client.put(
        f"{ISSUES_URL}/{base_issues['assigned']['id']}",
        json={"title": "Member edit attempt", "description": "Should not happen"},
        headers=auth(tokens["assignee"]),
    )
    assert response.status_code == 403
    assert "administrators" in response.json()["detail"]


def test_edit_issue_by_unrelated_member_forbidden(client, tokens, base_issues):
    response = client.put(
        f"{ISSUES_URL}/{base_issues['open']['id']}",
        json={"title": "Hijacked title", "description": "Should not happen"},
        headers=auth(tokens["outsider"]),
    )
    assert response.status_code == 403
    assert "administrators" in response.json()["detail"]


def test_edit_issue_by_admin_allowed(client, tokens, base_issues):
    response = client.put(
        f"{ISSUES_URL}/{base_issues['open']['id']}",
        json={"title": "Base issue open (admin edit)", "description": "Admin override"},
        headers=auth(tokens["admin"]),
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Base issue open (admin edit)"


def test_edit_issue_rejects_nonexistent_assignee(client, tokens, base_issues):
    response = client.put(
        f"{ISSUES_URL}/{base_issues['open']['id']}",
        json={"title": "Still valid title", "description": "", "assignee_id": 999999},
        headers=auth(tokens["admin"]),
    )
    assert response.status_code == 400


def test_edit_missing_issue_returns_404(client, tokens):
    response = client.put(
        f"{ISSUES_URL}/999999",
        json={"title": "No such issue", "description": ""},
        headers=auth(tokens["admin"]),
    )
    assert response.status_code == 404


# --- Status updates ----------------------------------------------------------------


def test_update_status_endpoint_as_admin(client, tokens, base_issues):
    issue_id = base_issues["open"]["id"]
    response = client.patch(
        f"{ISSUES_URL}/{issue_id}/status",
        json={"status": "in_progress"},
        headers=auth(tokens["admin"]),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_update_status_endpoint_as_assignee(client, tokens, base_issues):
    """The regular user a task is assigned to may change its status."""
    issue_id = base_issues["assigned"]["id"]
    response = client.patch(
        f"{ISSUES_URL}/{issue_id}/status",
        json={"status": "in_progress"},
        headers=auth(tokens["assignee"]),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"

    # ...back to open.
    response = client.patch(
        f"{ISSUES_URL}/{issue_id}/status",
        json={"status": "open"},
        headers=auth(tokens["assignee"]),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "open"


def test_update_status_rejects_invalid_value(client, tokens, base_issues):
    response = client.patch(
        f"{ISSUES_URL}/{base_issues['open']['id']}/status",
        json={"status": "archived"},
        headers=auth(tokens["admin"]),
    )
    assert response.status_code == 422


def test_update_status_by_unassigned_member_forbidden(client, tokens, base_issues):
    response = client.patch(
        f"{ISSUES_URL}/{base_issues['open']['id']}/status",
        json={"status": "closed"},
        headers=auth(tokens["outsider"]),
    )
    assert response.status_code == 403


# --- Assignment (admin only) ---------------------------------------------------------


def test_assign_issue_to_registered_user(client, tokens, user_ids, base_issues):
    issue_id = base_issues["closed"]["id"]
    response = client.patch(
        f"{ISSUES_URL}/{issue_id}/assign",
        json={"assignee_id": user_ids["assignee"]},
        headers=auth(tokens["admin"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["assignee"]["id"] == user_ids["assignee"]


def test_unassign_issue(client, tokens, base_issues):
    issue_id = base_issues["closed"]["id"]
    response = client.patch(
        f"{ISSUES_URL}/{issue_id}/assign",
        json={"assignee_id": None},
        headers=auth(tokens["admin"]),
    )
    assert response.status_code == 200
    assert response.json()["assignee"] is None
    assert response.json()["assignee_id"] is None


def test_assign_issue_to_nonexistent_user_rejected(client, tokens, base_issues):
    response = client.patch(
        f"{ISSUES_URL}/{base_issues['closed']['id']}/assign",
        json={"assignee_id": 424242},
        headers=auth(tokens["admin"]),
    )
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]


def test_assign_issue_by_member_forbidden(client, tokens, user_ids, base_issues):
    response = client.patch(
        f"{ISSUES_URL}/{base_issues['open']['id']}/assign",
        json={"assignee_id": user_ids["outsider"]},
        headers=auth(tokens["outsider"]),
    )
    assert response.status_code == 403
    assert "administrators" in response.json()["detail"]


# --- Deletion ------------------------------------------------------------------------


def test_delete_issue_by_member_forbidden(client, tokens, base_issues):
    response = client.delete(
        f"{ISSUES_URL}/{base_issues['open']['id']}", headers=auth(tokens["outsider"])
    )
    assert response.status_code == 403
    assert "administrators" in response.json()["detail"]


def test_delete_issue_by_admin(client, tokens):
    created = client.post(
        ISSUES_URL,
        json={"title": "Throwaway issue for delete", "description": "Gone soon"},
        headers=auth(tokens["admin"]),
    )
    assert created.status_code == 201
    issue_id = created.json()["id"]

    # A regular user still cannot delete it.
    assert client.delete(f"{ISSUES_URL}/{issue_id}", headers=auth(tokens["reporter"])).status_code == 403

    assert client.delete(f"{ISSUES_URL}/{issue_id}", headers=auth(tokens["admin"])).status_code == 204
    assert client.get(f"{ISSUES_URL}/{issue_id}", headers=auth(tokens["admin"])).status_code == 404
    # Deleting again now targets a missing issue.
    assert client.delete(f"{ISSUES_URL}/{issue_id}", headers=auth(tokens["admin"])).status_code == 404


# --- Comments against the real database -----------------------------------------------


def test_comments_persisted_and_chronological(client, tokens):
    """Comments must be stored in the database (author + timestamps) and listed
    in chronological order."""
    headers = auth(tokens["admin"])
    issue = client.post(
        ISSUES_URL,
        json={"title": "Comment ordering probe", "priority": "low"},
        headers=headers,
    ).json()

    for index in range(3):
        response = client.post(
            f"{ISSUES_URL}/{issue['id']}/comments",
            json={"content": f"comment {index}"},
            headers=headers,
        )
        assert response.status_code == 201, response.text

    listed = client.get(f"{ISSUES_URL}/{issue['id']}/comments", headers=headers).json()
    assert [comment["content"] for comment in listed] == ["comment 0", "comment 1", "comment 2"]
    created_timestamps = [comment["created_at"] for comment in listed]
    assert created_timestamps == sorted(created_timestamps)
    assert all(comment["author"]["email"] == USERS["admin"]["email"] for comment in listed)

    # Verify the rows actually exist in the database with author and timestamps.
    db = SessionLocal()
    try:
        rows = db.query(Comment).filter(Comment.issue_id == issue["id"]).all()
        assert len(rows) == 3
        assert {row.content for row in rows} == {"comment 0", "comment 1", "comment 2"}
        assert all(row.user_id == issue["reporter_id"] for row in rows)
        assert all(row.created_at is not None for row in rows)
    finally:
        db.close()


# --- Listing: pagination, filters, search ------------------------------------------------


def test_list_issues_requires_authentication(client):
    assert client.get(ISSUES_URL).status_code == 401


def test_list_users_returns_registered_users(client, tokens):
    # Admins can list users (needed for assignment pickers).
    response = client.get(USERS_URL, headers=auth(tokens["admin"]))
    assert response.status_code == 200
    emails = {user["email"] for user in response.json()}
    assert {payload["email"] for payload in USERS.values()} <= emails

    # Regular users cannot.
    assert client.get(USERS_URL, headers=auth(tokens["reporter"])).status_code == 403


def test_list_pagination(client, tokens):
    headers = auth(tokens["admin"])
    for index in range(5):
        client.post(
            ISSUES_URL,
            json={"title": f"Pagination filler {index:02d}", "priority": "low"},
            headers=headers,
        )

    first = client.get(ISSUES_URL, params={"page": 1, "page_size": 3}, headers=headers).json()
    assert first["page"] == 1
    assert first["page_size"] == 3
    assert len(first["items"]) == 3
    assert first["total"] >= 8

    second = client.get(ISSUES_URL, params={"page": 2, "page_size": 3}, headers=headers).json()
    assert second["page"] == 2
    assert not {item["id"] for item in first["items"]} & {item["id"] for item in second["items"]}

    empty = client.get(ISSUES_URL, params={"page": 999, "page_size": 3}, headers=headers).json()
    assert empty["items"] == []


def test_list_status_filter_and_search(client, tokens):
    headers = auth(tokens["admin"])
    probe = client.post(
        ISSUES_URL,
        json={"title": "Status filter probe zebrastatus", "description": "Unique probe"},
        headers=headers,
    ).json()
    client.patch(
        f"{ISSUES_URL}/{probe['id']}/status", json={"status": "closed"}, headers=headers
    )

    data = client.get(
        ISSUES_URL,
        params={"status": "closed", "search": "zebrastatus"},
        headers=headers,
    ).json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == probe["id"]

    # Open status no longer matches the closed probe.
    open_data = client.get(
        ISSUES_URL,
        params={"status": "open", "search": "zebrastatus"},
        headers=headers,
    ).json()
    assert open_data["total"] == 0

    # Invalid status values are rejected by validation.
    assert client.get(ISSUES_URL, params={"status": "bogus"}, headers=headers).status_code == 422


def test_list_assignee_filters(client, tokens, user_ids):
    headers = auth(tokens["admin"])
    assigned_probe = client.post(
        ISSUES_URL,
        json={
            "title": "Assignee filter probe zebrafilter",
            "assignee_id": user_ids["assignee"],
        },
        headers=headers,
    ).json()
    unassigned_probe = client.post(
        ISSUES_URL,
        json={"title": "Assignee filter probe zebrafilter unassigned"},
        headers=headers,
    ).json()

    by_assignee = client.get(
        ISSUES_URL,
        params={"assignee_id": user_ids["assignee"], "search": "zebrafilter"},
        headers=headers,
    ).json()
    assert by_assignee["total"] == 1
    assert by_assignee["items"][0]["id"] == assigned_probe["id"]

    unassigned = client.get(
        ISSUES_URL,
        params={"unassigned": "true", "search": "zebrafilter"},
        headers=headers,
    ).json()
    assert unassigned["total"] == 1
    assert unassigned["items"][0]["id"] == unassigned_probe["id"]


def test_list_search_matches_description_case_insensitively(client, tokens):
    headers = auth(tokens["admin"])
    client.post(
        ISSUES_URL,
        json={"title": "Search probe one", "description": "Contains QuantumTeapot somewhere"},
        headers=headers,
    )
    data = client.get(ISSUES_URL, params={"search": "quantumteapot"}, headers=headers).json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Search probe one"
