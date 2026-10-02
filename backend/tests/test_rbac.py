"""RBAC enforcement tests.

Rules under test:
- Only the Admin can create, edit, delete and assign issues/tasks.
- Regular users can never assign tasks (to themselves, the admin, or others).
- Regular users only see tasks assigned to them and may update their status
  between open / in_progress / closed.
- The Admin sees and manages all tasks.
- All of this is enforced on the backend APIs themselves.
"""

import pytest

from app.db.session import SessionLocal
from app.models.user import User, UserRole

ISSUES_URL = "/api/issues"
USERS_URL = "/api/users"
DASHBOARD_URL = "/api/dashboard/summary"
PASSWORD = "supersecret123"

USERS = {
    "root": {"name": "Root Admin", "email": "root@example.com"},
    "sam": {"name": "Sam Member", "email": "sam@example.com"},
    "sara": {"name": "Sara Member", "email": "sara@example.com"},
}


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def tokens(client):
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

    # Promote root to admin directly in the database (no public role API).
    db = SessionLocal()
    try:
        root = db.query(User).filter(User.email == USERS["root"]["email"]).first()
        assert root is not None
        root.role = UserRole.ADMIN
        db.commit()
    finally:
        db.close()
    return result


@pytest.fixture(scope="module")
def user_ids(client, tokens):
    users = client.get(USERS_URL, headers=auth(tokens["root"])).json()
    return {
        key: next(user["id"] for user in users if user["email"] == payload["email"])
        for key, payload in USERS.items()
    }


@pytest.fixture(scope="module")
def tasks(client, tokens, user_ids):
    """Three tasks created by the admin: assigned to sam, to sara, unassigned."""
    root = auth(tokens["root"])

    to_sam = client.post(
        ISSUES_URL,
        json={"title": "RBAC task for sam", "priority": "medium", "assignee_id": user_ids["sam"]},
        headers=root,
    )
    assert to_sam.status_code == 201, to_sam.text

    to_sara = client.post(
        ISSUES_URL,
        json={"title": "RBAC task for sara", "priority": "low", "assignee_id": user_ids["sara"]},
        headers=root,
    )
    assert to_sara.status_code == 201, to_sara.text

    unassigned = client.post(
        ISSUES_URL,
        json={"title": "RBAC unassigned task", "priority": "low"},
        headers=root,
    )
    assert unassigned.status_code == 201, unassigned.text

    return {
        "sam": to_sam.json(),
        "sara": to_sara.json(),
        "unassigned": unassigned.json(),
    }


# --- Members cannot create issues -------------------------------------------------


def test_member_cannot_create_issue(client, tokens):
    response = client.post(
        ISSUES_URL,
        json={"title": "Member created this", "priority": "low"},
        headers=auth(tokens["sam"]),
    )
    assert response.status_code == 403
    assert "administrators" in response.json()["detail"]


# --- Members only see tasks assigned to them ---------------------------------------


def test_member_list_contains_only_their_assigned_tasks(client, tokens, tasks, user_ids):
    data = client.get(ISSUES_URL, headers=auth(tokens["sam"])).json()
    assignee_ids = {item["assignee_id"] for item in data["items"]}
    assert data["total"] == len(data["items"])
    assert assignee_ids == {user_ids["sam"]}
    assert {item["id"] for item in data["items"]} == {tasks["sam"]["id"]}


def test_member_filters_cannot_leak_other_users_tasks(client, tokens, tasks):
    # Searching for another user's task title yields nothing (scope wins).
    data = client.get(
        ISSUES_URL, params={"search": "RBAC task for sara"}, headers=auth(tokens["sam"])
    ).json()
    assert data["total"] == 0

    # Filtering by another assignee yields nothing either.
    data = client.get(
        ISSUES_URL, params={"assignee_id": tasks["sara"]["assignee_id"]}, headers=auth(tokens["sam"])
    ).json()
    assert data["total"] == 0

    # Admin sees everything.
    admin_data = client.get(ISSUES_URL, headers=auth(tokens["root"])).json()
    seen = {item["id"] for item in admin_data["items"]}
    assert {tasks["sam"]["id"], tasks["sara"]["id"], tasks["unassigned"]["id"]} <= seen


def test_member_view_access(client, tokens, tasks):
    assert (
        client.get(f"{ISSUES_URL}/{tasks['sam']['id']}", headers=auth(tokens["sam"])).status_code
        == 200
    )

    forbidden = client.get(
        f"{ISSUES_URL}/{tasks['sara']['id']}", headers=auth(tokens["sam"])
    )
    assert forbidden.status_code == 403
    assert "do not have access" in forbidden.json()["detail"]

    assert (
        client.get(
            f"{ISSUES_URL}/{tasks['unassigned']['id']}", headers=auth(tokens["sam"])
        ).status_code
        == 403
    )


# --- Members can update status of their own tasks ----------------------------------


def test_member_updates_status_between_all_three_values(client, tokens, tasks):
    issue_id = tasks["sam"]["id"]
    headers = auth(tokens["sam"])

    for value in ("in_progress", "closed", "open"):
        response = client.patch(
            f"{ISSUES_URL}/{issue_id}/status", json={"status": value}, headers=headers
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == value


def test_member_cannot_update_status_of_other_tasks(client, tokens, tasks):
    assert (
        client.patch(
            f"{ISSUES_URL}/{tasks['sara']['id']}/status",
            json={"status": "closed"},
            headers=auth(tokens["sam"]),
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"{ISSUES_URL}/{tasks['unassigned']['id']}/status",
            json={"status": "closed"},
            headers=auth(tokens["sam"]),
        ).status_code
        == 403
    )


# --- Members can never assign -------------------------------------------------------


def test_member_cannot_assign_to_self_admin_or_others(client, tokens, tasks, user_ids):
    issue_id = tasks["sam"]["id"]
    headers = auth(tokens["sam"])

    for target in (user_ids["sam"], user_ids["root"], user_ids["sara"]):
        response = client.patch(
            f"{ISSUES_URL}/{issue_id}/assign", json={"assignee_id": target}, headers=headers
        )
        assert response.status_code == 403, response.text
        assert "administrators" in response.json()["detail"]

    # Sneaking an assignee through edit endpoints is blocked too.
    assert (
        client.put(
            f"{ISSUES_URL}/{issue_id}",
            json={"title": "RBAC task for sam", "description": "", "assignee_id": user_ids["sam"]},
            headers=headers,
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"{ISSUES_URL}/{issue_id}", json={"assignee_id": user_ids["sam"]}, headers=headers
        ).status_code
        == 403
    )


# --- Members cannot edit or delete ---------------------------------------------------


def test_member_cannot_edit_or_delete(client, tokens, tasks):
    issue_id = tasks["sam"]["id"]
    headers = auth(tokens["sam"])

    assert (
        client.put(
            f"{ISSUES_URL}/{issue_id}",
            json={"title": "Member rewrote this", "description": ""},
            headers=headers,
        ).status_code
        == 403
    )
    assert (
        client.patch(f"{ISSUES_URL}/{issue_id}", json={"title": "Member retitled"}, headers=headers).status_code
        == 403
    )
    assert client.delete(f"{ISSUES_URL}/{issue_id}", headers=headers).status_code == 403

    # The task is untouched.
    current = client.get(f"{ISSUES_URL}/{issue_id}", headers=headers).json()
    assert current["title"] == "RBAC task for sam"


# --- User list is admin-only -----------------------------------------------------------


def test_member_cannot_list_users(client, tokens):
    response = client.get(USERS_URL, headers=auth(tokens["sam"]))
    assert response.status_code == 403
    assert "administrators" in response.json()["detail"]
    assert client.get(USERS_URL, headers=auth(tokens["root"])).status_code == 200


# --- Comments scoped like viewing -------------------------------------------------------


def test_member_comments_only_on_their_tasks(client, tokens, tasks):
    assert (
        client.post(
            f"{ISSUES_URL}/{tasks['sam']['id']}/comments",
            json={"content": "Working on it."},
            headers=auth(tokens["sam"]),
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"{ISSUES_URL}/{tasks['sara']['id']}/comments",
            json={"content": "Should not be allowed"},
            headers=auth(tokens["sam"]),
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"{ISSUES_URL}/{tasks['sara']['id']}/comments", headers=auth(tokens["sam"])
        ).status_code
        == 403
    )


# --- Dashboard is scoped for members ------------------------------------------------------


def test_member_dashboard_counts_only_their_tasks(client, tokens, tasks, user_ids):
    summary = client.get(DASHBOARD_URL, headers=auth(tokens["sam"])).json()

    assert summary["total_issues"] == 1
    assert summary["open_issues"] + summary["in_progress_issues"] + summary["closed_issues"] == 1
    assert {item["id"] for item in summary["recent_issues"]} == {tasks["sam"]["id"]}
    assert {item["id"] for item in summary["my_assigned_issues"]} == {tasks["sam"]["id"]}
    assert all(item["assignee_id"] == user_ids["sam"] for item in summary["recent_issues"])


def test_admin_dashboard_counts_all_tasks(client, tokens, tasks):
    summary = client.get(DASHBOARD_URL, headers=auth(tokens["root"])).json()

    seen = {item["id"] for item in summary["recent_issues"]}
    assert {tasks["sam"]["id"], tasks["sara"]["id"], tasks["unassigned"]["id"]} <= seen
    assert summary["total_issues"] >= 3
    assert (
        summary["open_issues"] + summary["in_progress_issues"] + summary["closed_issues"]
        == summary["total_issues"]
    )


# --- Admin can manage all tasks ------------------------------------------------------------


def test_admin_creates_edits_assigns_deletes(client, tokens, tasks, user_ids):
    root = auth(tokens["root"])

    # Edit any task (including one assigned to someone else).
    edited = client.put(
        f"{ISSUES_URL}/{tasks['sara']['id']}",
        json={"title": "RBAC task for sara (admin edit)", "description": "Retitled by admin"},
        headers=root,
    )
    assert edited.status_code == 200
    assert edited.json()["title"] == "RBAC task for sara (admin edit)"

    # Assign the unassigned task.
    assigned = client.patch(
        f"{ISSUES_URL}/{tasks['unassigned']['id']}/assign",
        json={"assignee_id": user_ids["sara"]},
        headers=root,
    )
    assert assigned.status_code == 200
    assert assigned.json()["assignee"]["id"] == user_ids["sara"]

    # Change status of any task.
    assert (
        client.patch(
            f"{ISSUES_URL}/{tasks['sam']['id']}/status",
            json={"status": "closed"},
            headers=root,
        ).status_code
        == 200
    )

    # Delete any task.
    assert (
        client.delete(f"{ISSUES_URL}/{tasks['unassigned']['id']}", headers=root).status_code == 204
    )
    assert client.get(f"{ISSUES_URL}/{tasks['unassigned']['id']}", headers=root).status_code == 404
