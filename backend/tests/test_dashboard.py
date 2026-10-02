"""Tests for the dashboard summary endpoint, verified against the real database."""

import pytest

from app.db.session import SessionLocal
from app.models.user import User, UserRole

DASHBOARD_URL = "/api/dashboard/summary"
ISSUES_URL = "/api/issues"
USERS_URL = "/api/users"
PASSWORD = "supersecret123"

USERS = {
    "dana": {"name": "Dana Dashboard", "email": "dana@example.com"},
    "marta": {"name": "Marta Member", "email": "marta@example.com"},
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

    # Dana drives the global dashboard counters, so she must be an admin
    # (under RBAC only admins see and count all issues). Marta stays a member
    # to verify the member-scoped dashboard.
    db = SessionLocal()
    try:
        dana = db.query(User).filter(User.email == USERS["dana"]["email"]).first()
        assert dana is not None
        dana.role = UserRole.ADMIN
        db.commit()
    finally:
        db.close()
    return result


@pytest.fixture(scope="module")
def user_ids(client, tokens):
    users = client.get(USERS_URL, headers=auth(tokens["dana"])).json()
    return {
        key: next(user["id"] for user in users if user["email"] == payload["email"])
        for key, payload in USERS.items()
    }


def _summary(client, token: str) -> dict:
    response = client.get(DASHBOARD_URL, headers=auth(token))
    assert response.status_code == 200, response.text
    return response.json()


# --- Access control -------------------------------------------------------------


def test_summary_requires_authentication(client):
    assert client.get(DASHBOARD_URL).status_code == 401


# --- Counts computed from the database -------------------------------------------


def test_counts_reflect_database_changes(client, tokens):
    before = _summary(client, tokens["dana"])
    headers = auth(tokens["dana"])

    open_one = client.post(ISSUES_URL, json={"title": "Dash count open one"}, headers=headers)
    open_two = client.post(ISSUES_URL, json={"title": "Dash count open two"}, headers=headers)
    in_progress = client.post(ISSUES_URL, json={"title": "Dash count progress"}, headers=headers)
    closed = client.post(ISSUES_URL, json={"title": "Dash count closed"}, headers=headers)
    assert all(r.status_code == 201 for r in (open_one, open_two, in_progress, closed))

    assert (
        client.patch(
            f"{ISSUES_URL}/{in_progress.json()['id']}/status",
            json={"status": "in_progress"},
            headers=headers,
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"{ISSUES_URL}/{closed.json()['id']}/status",
            json={"status": "closed"},
            headers=headers,
        ).status_code
        == 200
    )

    after = _summary(client, tokens["dana"])

    assert after["total_issues"] == before["total_issues"] + 4
    assert after["open_issues"] == before["open_issues"] + 2
    assert after["in_progress_issues"] == before["in_progress_issues"] + 1
    assert after["closed_issues"] == before["closed_issues"] + 1
    # The four per-status counts must add up to the total.
    assert (
        after["open_issues"] + after["in_progress_issues"] + after["closed_issues"]
        == after["total_issues"]
    )


def test_counts_update_after_edit_and_delete(client, tokens):
    headers = auth(tokens["dana"])
    before = _summary(client, tokens["dana"])

    probe = client.post(
        ISSUES_URL, json={"title": "Dash delete probe", "priority": "low"}, headers=headers
    )
    issue_id = probe.json()["id"]
    middle = _summary(client, tokens["dana"])
    assert middle["total_issues"] == before["total_issues"] + 1

    # Editing an issue must not change any counts (only the issue's own data).
    edited = client.put(
        f"{ISSUES_URL}/{issue_id}",
        json={"title": "Dash delete probe (edited)", "description": "Renamed"},
        headers=headers,
    )
    assert edited.status_code == 200
    after_edit = _summary(client, tokens["dana"])
    for counter in (
        "total_issues",
        "open_issues",
        "in_progress_issues",
        "closed_issues",
    ):
        assert after_edit[counter] == middle[counter]
    # The edited title shows up in the dashboard's recent issues.
    assert issue_id in {item["id"] for item in after_edit["recent_issues"]}
    assert any(item["title"] == "Dash delete probe (edited)" for item in after_edit["recent_issues"])

    # Deleting the issue must bring the total back down.
    assert client.delete(f"{ISSUES_URL}/{issue_id}", headers=headers).status_code == 204
    after_delete = _summary(client, tokens["dana"])
    assert after_delete["total_issues"] == before["total_issues"]
    assert after_delete["open_issues"] == before["open_issues"]


# --- Recent issues ----------------------------------------------------------------


def test_recent_issues_are_newest_first_with_details(client, tokens):
    headers = auth(tokens["dana"])
    created_ids = []
    for index in range(3):
        response = client.post(
            ISSUES_URL,
            json={"title": f"Dash recent probe {index}", "priority": "low"},
            headers=headers,
        )
        created_ids.append(response.json()["id"])

    summary = _summary(client, tokens["dana"])
    recent = summary["recent_issues"]

    assert len(recent) <= 5
    assert recent[0]["id"] == created_ids[-1]  # newest first

    timestamps = [item["created_at"] for item in recent]
    assert timestamps == sorted(timestamps, reverse=True)

    # Every recent issue carries reporter/assignee details for the table view.
    newest = recent[0]
    assert newest["reporter"]["email"] == USERS["dana"]["email"]
    assert "assignee" in newest and "created_at" in newest


def test_my_assigned_issues(client, tokens, user_ids):
    headers = auth(tokens["dana"])
    marta_headers = auth(tokens["marta"])

    mine_before = _summary(client, tokens["marta"])["my_assigned_issues"]

    probe = client.post(
        ISSUES_URL,
        json={"title": "Dash assigned probe", "priority": "high"},
        headers=headers,
    )
    issue_id = probe.json()["id"]
    assert (
        client.patch(
            f"{ISSUES_URL}/{issue_id}/assign",
            json={"assignee_id": user_ids["marta"]},
            headers=headers,
        ).status_code
        == 200
    )

    marta_assigned = _summary(client, tokens["marta"])["my_assigned_issues"]
    assert issue_id in {item["id"] for item in marta_assigned}
    assert len(marta_assigned) == len(mine_before) + 1
    # It must not appear in other users' lists.
    assert issue_id not in {item["id"] for item in _summary(client, tokens["dana"])["my_assigned_issues"]}

    # Closed issues drop out of the assigned list (they are no longer actionable).
    assert (
        client.patch(
            f"{ISSUES_URL}/{issue_id}/status", json={"status": "closed"}, headers=headers
        ).status_code
        == 200
    )
    assert issue_id not in {
        item["id"] for item in _summary(client, tokens["marta"])["my_assigned_issues"]
    }
