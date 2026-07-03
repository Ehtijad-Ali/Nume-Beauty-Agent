"""Tests for products CRUD."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _auth_headers(client: TestClient, email: str = "p@nume.ai", password: str = "Pass1234A") -> dict:
    """Register + login a user, return Authorization headers."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "P"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    ).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def test_create_product(client: TestClient, seed_roles) -> None:
    """POST /products creates a product and returns 201."""
    headers = _auth_headers(client)
    response = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Aurora Serum",
            "sku": "NUM-SRM-001",
            "category": "Skincare",
            "price": "78.00",
            "stock": 100,
            "status": "active",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Aurora Serum"
    assert body["sku"] == "NUM-SRM-001"


def test_create_duplicate_sku_conflict(client: TestClient, seed_roles) -> None:
    """Creating two products with the same SKU returns 409."""
    headers = _auth_headers(client)
    payload = {"name": "A", "sku": "DUP", "price": "10"}
    client.post("/api/v1/products", headers=headers, json=payload)
    response = client.post("/api/v1/products", headers=headers, json=payload)
    assert response.status_code == 409


def test_list_products(client: TestClient, seed_roles) -> None:
    """GET /products returns paginated list."""
    headers = _auth_headers(client)
    for i in range(3):
        client.post(
            "/api/v1/products",
            headers=headers,
            json={"name": f"P{i}", "sku": f"SKU-{i}", "price": "10"},
        )
    response = client.get("/api/v1/products", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_get_product(client: TestClient, seed_roles) -> None:
    """GET /products/{id} returns the product."""
    headers = _auth_headers(client)
    created = client.post(
        "/api/v1/products",
        headers=headers,
        json={"name": "X", "sku": "X1", "price": "5"},
    ).json()
    response = client.get(f"/api/v1/products/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_product(client: TestClient, seed_roles) -> None:
    """PATCH /products/{id} updates fields."""
    headers = _auth_headers(client)
    created = client.post(
        "/api/v1/products",
        headers=headers,
        json={"name": "Old", "sku": "OLD1", "price": "5"},
    ).json()
    response = client.patch(
        f"/api/v1/products/{created['id']}",
        headers=headers,
        json={"name": "New", "price": "15.00"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New"
    assert body["price"] == "15.00"


def test_delete_product(client: TestClient, seed_roles) -> None:
    """DELETE /products/{id} removes the product."""
    headers = _auth_headers(client)
    created = client.post(
        "/api/v1/products",
        headers=headers,
        json={"name": "D", "sku": "D1", "price": "5"},
    ).json()
    response = client.delete(f"/api/v1/products/{created['id']}", headers=headers)
    assert response.status_code == 200
    # Subsequent GET should 404
    response = client.get(f"/api/v1/products/{created['id']}", headers=headers)
    assert response.status_code == 404
