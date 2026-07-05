"""Tests for the Phase 2.1 knowledge base API (upload, versions, categories)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config.settings import get_settings


@pytest.fixture(autouse=True)
def isolated_upload_dir(tmp_path, monkeypatch):
    """Point file storage at a temp dir so tests don't touch ./uploads."""
    monkeypatch.setattr(get_settings(), "upload_path", str(tmp_path))
    yield


def _auth_headers(client: TestClient, email: str = "kb@nume.ai", password: str = "Pass1234A") -> dict:
    """Register + login a user, return Authorization headers."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "KB Tester"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    ).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def _upload_txt(client: TestClient, headers: dict, *, name: str = "brand-voice.txt", **form) -> dict:
    body = ("NUMÉ brand voice guide. " * 100).encode("utf-8")
    response = client.post(
        "/api/v1/knowledge/upload",
        headers=headers,
        files={"file": (name, body, "text/plain")},
        data=form,
    )
    assert response.status_code == 201, response.text
    return response.json()


# --------------------------------------------------------------------------- #
# Upload + ingestion
# --------------------------------------------------------------------------- #
def test_upload_txt_document_is_ingested(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload_txt(client, headers, tags="brand,voice", brand="NUMÉ")

    assert doc["status"] == "ready"
    assert doc["doc_type"] == "txt"
    assert doc["version"] == 1
    assert doc["chunk_count"] > 0
    assert doc["word_count"] > 0
    assert doc["excerpt"]
    assert doc["tags"] == "brand,voice"
    assert doc["brand"] == "NUMÉ"
    assert doc["original_filename"] == "brand-voice.txt"
    assert doc["uploaded_by"]["full_name"] == "KB Tester"
    assert doc["last_indexed_at"] is not None
    # Auto-categorised from the "brand" keywords
    assert doc["category"] is not None
    assert doc["category"]["slug"] == "brand-guidelines"


def test_upload_csv_document_stores_metadata(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    body = b"name,price\nAurora Serum,78\nVelvet Tint,29\n"
    response = client.post(
        "/api/v1/knowledge/upload",
        headers=headers,
        files={"file": ("catalog.csv", body, "text/csv")},
        data={"title": "Product Catalog"},
    )
    assert response.status_code == 201, response.text
    doc = response.json()
    assert doc["title"] == "Product Catalog"
    assert doc["doc_type"] == "csv"
    assert doc["status"] == "ready"
    assert doc["doc_metadata"]["columns"] == ["name", "price"]
    assert doc["doc_metadata"]["row_count"] == 2


def test_upload_unsupported_type_is_rejected(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    response = client.post(
        "/api/v1/knowledge/upload",
        headers=headers,
        files={"file": ("archive.zip", b"PK\x03\x04", "application/zip")},
    )
    assert response.status_code == 400


def test_upload_requires_auth(client: TestClient, seed_roles) -> None:
    response = client.post(
        "/api/v1/knowledge/upload",
        files={"file": ("a.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 401


# --------------------------------------------------------------------------- #
# Chunks & versions
# --------------------------------------------------------------------------- #
def test_chunks_endpoint_returns_ordered_chunks(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload_txt(client, headers)
    response = client.get(f"/api/v1/knowledge/{doc['id']}/chunks", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == doc["chunk_count"]
    indexes = [c["chunk_index"] for c in body["items"]]
    assert indexes == sorted(indexes)
    assert all(c["content"] for c in body["items"])


def test_replace_document_bumps_version_and_reingests(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload_txt(client, headers)

    new_body = b"name,price\nHydra Toner,19\n"
    response = client.post(
        f"/api/v1/knowledge/{doc['id']}/replace",
        headers=headers,
        files={"file": ("catalog-v2.csv", new_body, "text/csv")},
        data={"change_note": "Swapped to catalog"},
    )
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["version"] == 2
    assert updated["doc_type"] == "csv"
    assert updated["status"] == "ready"
    assert updated["original_filename"] == "catalog-v2.csv"

    versions = client.get(f"/api/v1/knowledge/{doc['id']}/versions", headers=headers).json()
    assert [v["version"] for v in versions] == [2, 1]
    assert versions[0]["change_note"] == "Swapped to catalog"
    assert versions[1]["change_note"] == "Initial upload"


def test_reindex_document(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload_txt(client, headers)
    response = client.post(f"/api/v1/knowledge/{doc['id']}/reindex", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ready"
    assert body["chunk_count"] == doc["chunk_count"]


def test_delete_document_removes_chunks_and_versions(client: TestClient, seed_roles, db_session) -> None:
    headers = _auth_headers(client)
    doc = _upload_txt(client, headers)

    response = client.delete(f"/api/v1/knowledge/{doc['id']}", headers=headers)
    assert response.status_code == 200
    assert client.get(f"/api/v1/knowledge/{doc['id']}", headers=headers).status_code == 404

    from app.models.document_chunk import DocumentChunk
    from app.models.document_version import DocumentVersion

    assert db_session.query(DocumentChunk).count() == 0
    assert db_session.query(DocumentVersion).count() == 0


def test_download_document(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload_txt(client, headers)
    response = client.get(f"/api/v1/knowledge/{doc['id']}/download", headers=headers)
    assert response.status_code == 200
    assert "NUMÉ brand voice guide." in response.content.decode("utf-8")


# --------------------------------------------------------------------------- #
# Filters & search
# --------------------------------------------------------------------------- #
def test_list_filters_by_type_category_and_search(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    _upload_txt(client, headers, name="voice.txt")
    csv_doc = client.post(
        "/api/v1/knowledge/upload",
        headers=headers,
        files={"file": ("report-q1.csv", b"kpi,value\nrevenue,100\n", "text/csv")},
    ).json()

    by_type = client.get("/api/v1/knowledge?doc_type=csv", headers=headers).json()
    assert by_type["total"] == 1
    assert by_type["items"][0]["id"] == csv_doc["id"]

    by_category = client.get(
        f"/api/v1/knowledge?category_id={csv_doc['category_id']}", headers=headers
    ).json()
    assert any(item["id"] == csv_doc["id"] for item in by_category["items"])

    by_search = client.get("/api/v1/knowledge?search=voice", headers=headers).json()
    assert by_search["total"] == 1
    assert by_search["items"][0]["doc_type"] == "txt"


# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #
def test_category_crud(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)

    created = client.post(
        "/api/v1/knowledge/categories",
        headers=headers,
        json={"name": "Tutorials", "description": "How-to guides", "color": "#123456"},
    )
    assert created.status_code == 201, created.text
    category = created.json()
    assert category["slug"] == "tutorials"

    duplicate = client.post(
        "/api/v1/knowledge/categories", headers=headers, json={"name": "Tutorials"}
    )
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/v1/knowledge/categories/{category['id']}",
        headers=headers,
        json={"name": "Guides & Tutorials"},
    )
    assert updated.status_code == 200
    assert updated.json()["slug"] == "guides-tutorials"

    listed = client.get("/api/v1/knowledge/categories", headers=headers).json()
    assert any(c["id"] == category["id"] for c in listed)

    deleted = client.delete(
        f"/api/v1/knowledge/categories/{category['id']}", headers=headers
    )
    assert deleted.status_code == 200


def test_deleting_category_keeps_documents(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload_txt(client, headers)
    category_id = doc["category_id"]
    assert category_id

    response = client.delete(f"/api/v1/knowledge/categories/{category_id}", headers=headers)
    assert response.status_code == 200

    refreshed = client.get(f"/api/v1/knowledge/{doc['id']}", headers=headers).json()
    assert refreshed["category_id"] is None
    assert refreshed["status"] == "ready"
