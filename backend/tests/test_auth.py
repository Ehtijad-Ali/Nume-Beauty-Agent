"""Tests for the authentication flow."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_first_user_becomes_admin(client: TestClient, seed_roles) -> None:
    """The first registered user should be a superuser + admin."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@nume.ai",
            "password": "OwnerPass123",
            "full_name": "Owner",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == "owner@nume.ai"
    assert body["is_superuser"] is True
    assert body["role"]["name"] == "admin"


def test_register_duplicate_email_fails(client: TestClient, seed_roles) -> None:
    """Registering the same email twice should return 409."""
    payload = {
        "email": "dup@nume.ai",
        "password": "DupPass123",
        "full_name": "Dup",
    }
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


def test_login_success(client: TestClient, seed_roles) -> None:
    """Login with valid credentials returns access + refresh tokens."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@nume.ai",
            "password": "LoginPass123",
            "full_name": "Login Test",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@nume.ai", "password": "LoginPass123"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "login@nume.ai"


def test_login_wrong_password(client: TestClient, seed_roles) -> None:
    """Login with wrong password returns 401."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong@nume.ai",
            "password": "RightPass123",
            "full_name": "Wrong",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@nume.ai", "password": "BadPass123"},
    )
    assert response.status_code == 401


def test_me_requires_auth(client: TestClient) -> None:
    """GET /auth/me without a token should return 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_token(client: TestClient, seed_roles) -> None:
    """GET /auth/me with a valid token returns the user."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@nume.ai",
            "password": "MePass123",
            "full_name": "Me",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "me@nume.ai", "password": "MePass123"},
    ).json()
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@nume.ai"


def test_refresh_token(client: TestClient, seed_roles) -> None:
    """Refresh endpoint issues a new access token."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@nume.ai",
            "password": "RefreshPass123",
            "full_name": "Refresh",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@nume.ai", "password": "RefreshPass123"},
    ).json()
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert response.status_code == 200, response.text
    assert "access_token" in response.json()


def test_logout_revokes_session(client: TestClient, seed_roles) -> None:
    """After logout, the refresh token can no longer be used."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "out@nume.ai",
            "password": "OutPass123",
            "full_name": "Out",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "out@nume.ai", "password": "OutPass123"},
    ).json()
    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login["refresh_token"]},
    )
    assert logout.status_code == 200
    # Refresh should now fail
    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert refresh.status_code == 401
