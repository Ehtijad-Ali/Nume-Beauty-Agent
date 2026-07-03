"""Tests for health endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_root(client: TestClient) -> None:
    """/ should return service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "service" in body
    assert "version" in body


def test_health(client: TestClient) -> None:
    """/health should return ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_healthz(client: TestClient) -> None:
    """/healthz should return ok."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
