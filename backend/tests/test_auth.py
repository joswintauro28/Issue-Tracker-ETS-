"""Tests for registration, login, token handling, protected endpoints and comments."""

import pytest

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.user import User, UserRole

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/auth/me"
ISSUES_URL = "/api/issues"
USERS_URL = "/api/users"

VALID_USER = {
    "name": "Test User",
    "email": "test.user@example.com",
    "password": "supersecret123",
    "confirm_password": "supersecret123",
}


@pytest.fixture(scope="module")
def registered_user(client):
    """Register one valid user used by the rest of the module's tests."""
    response = client.post(REGISTER_URL, json=VALID_USER)
    assert response.status_code == 201, response.text
    user = response.json()

    # The comment/cascade flows below exercise admin-managed issue operations
    # (create, delete), so promote this test user to admin in the database.
    # Registration itself still returned role=user (asserted by the test).
    db = SessionLocal()
    try:
        record = db.query(User).filter(User.email == VALID_USER["email"]).first()
        assert record is not None
        record.role = UserRole.ADMIN
        db.commit()
    finally:
        db.close()
    return user


def _login(client, email: str, password: str) -> dict:
    response = client.post(LOGIN_URL, json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


# --- Registration -----------------------------------------------------------


def test_register_success(client, registered_user):
    user = registered_user
    assert user["email"] == VALID_USER["email"]
    assert user["name"] == VALID_USER["name"]
    assert user["role"] == "user"


def test_register_response_never_exposes_password_hash(client, registered_user):
    body = registered_user
    assert "hashed_password" not in body
    assert "password" not in body


def test_register_duplicate_email(client, registered_user):
    response = client.post(REGISTER_URL, json=VALID_USER)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_register_password_mismatch(client):
    payload = {**VALID_USER, "email": "mismatch@example.com", "confirm_password": "different456"}
    response = client.post(REGISTER_URL, json=payload)
    assert response.status_code == 422
    assert any("Passwords do not match" in str(item) for item in response.json()["detail"])


def test_register_short_password(client):
    payload = {**VALID_USER, "email": "shortpw@example.com", "password": "short", "confirm_password": "short"}
    response = client.post(REGISTER_URL, json=payload)
    assert response.status_code == 422


def test_register_invalid_email(client):
    payload = {**VALID_USER, "email": "not-an-email"}
    response = client.post(REGISTER_URL, json=payload)
    assert response.status_code == 422


def test_register_missing_fields(client):
    response = client.post(REGISTER_URL, json={"name": "Incomplete User"})
    assert response.status_code == 422


# --- Login ------------------------------------------------------------------


def test_login_success(client, registered_user):
    token = _login(client, VALID_USER["email"], VALID_USER["password"])
    assert token["token_type"] == "bearer"
    assert len(token["access_token"]) > 20


def test_login_wrong_password(client, registered_user):
    response = client.post(LOGIN_URL, json={"email": VALID_USER["email"], "password": "wrongpassword"})
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_unknown_email(client):
    response = client.post(LOGIN_URL, json={"email": "ghost@example.com", "password": "whatever123"})
    assert response.status_code == 401


# --- Current user / protected endpoints -------------------------------------


def test_me_requires_authentication(client):
    response = client.get(ME_URL)
    assert response.status_code == 401


def test_me_returns_profile(client, registered_user):
    token = _login(client, VALID_USER["email"], VALID_USER["password"])
    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token['access_token']}"})
    assert response.status_code == 200
    assert response.json()["email"] == VALID_USER["email"]
    assert "hashed_password" not in response.json()


def test_me_with_garbage_token(client):
    response = client.get(ME_URL, headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_me_with_expired_token(client, registered_user):
    expired_token = create_access_token(subject=1, expires_minutes=-1)
    response = client.get(ME_URL, headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_issues_require_authentication(client):
    response = client.get(ISSUES_URL)
    assert response.status_code == 401


def test_users_require_authentication(client):
    response = client.get(USERS_URL)
    assert response.status_code == 401


def test_authenticated_user_can_list_issues_and_users(client, registered_user):
    token = _login(client, VALID_USER["email"], VALID_USER["password"])
    headers = {"Authorization": f"Bearer {token['access_token']}"}
    assert client.get(ISSUES_URL, headers=headers).status_code == 200
    assert client.get(USERS_URL, headers=headers).status_code == 200


# --- Comments ----------------------------------------------------------------


def test_comment_flow(client, registered_user):
    token = _login(client, VALID_USER["email"], VALID_USER["password"])
    headers = {"Authorization": f"Bearer {token['access_token']}"}

    created = client.post(
        ISSUES_URL,
        json={"title": "Issue for comments", "description": "Test issue", "priority": "low"},
        headers=headers,
    )
    assert created.status_code == 201
    issue_id = created.json()["id"]

    # Commenting requires authentication
    assert client.post(f"{ISSUES_URL}/{issue_id}/comments", json={"content": "anon"}).status_code == 401

    comment = client.post(
        f"{ISSUES_URL}/{issue_id}/comments",
        json={"content": "First comment"},
        headers=headers,
    )
    assert comment.status_code == 201
    body = comment.json()
    assert body["content"] == "First comment"
    assert body["author"]["email"] == VALID_USER["email"]
    assert "hashed_password" not in body["author"]

    listed = client.get(f"{ISSUES_URL}/{issue_id}/comments", headers=headers)
    assert listed.status_code == 200
    assert [item["content"] for item in listed.json()] == ["First comment"]

    # Blank comments are rejected
    assert (
        client.post(f"{ISSUES_URL}/{issue_id}/comments", json={"content": "   "}, headers=headers).status_code
        == 422
    )

    # Comments on a non-existent issue are rejected
    assert (
        client.post(f"{ISSUES_URL}/999999/comments", json={"content": "hi"}, headers=headers).status_code
        == 404
    )


def test_deleting_issue_cascades_comments(client, registered_user):
    token = _login(client, VALID_USER["email"], VALID_USER["password"])
    headers = {"Authorization": f"Bearer {token['access_token']}"}

    created = client.post(
        ISSUES_URL, json={"title": "Issue to delete", "priority": "low"}, headers=headers
    )
    issue_id = created.json()["id"]
    client.post(f"{ISSUES_URL}/{issue_id}/comments", json={"content": "will vanish"}, headers=headers)

    assert client.delete(f"{ISSUES_URL}/{issue_id}", headers=headers).status_code == 204
    assert client.get(f"{ISSUES_URL}/{issue_id}", headers=headers).status_code == 404
