"""Tests for Phase 2.2 — embedding jobs, Qdrant storage, semantic search."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config.settings import get_settings


@pytest.fixture(autouse=True)
def isolated_upload_dir(tmp_path, monkeypatch):
    """Point file storage at a temp dir so tests don't touch ./uploads."""
    monkeypatch.setattr(get_settings(), "upload_path", str(tmp_path))
    yield


def _auth_headers(client: TestClient, email: str = "vec@nume.ai", password: str = "Pass1234A") -> dict:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Vec Tester"},
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def _upload(client: TestClient, headers: dict, name: str, body: bytes, mime: str, **form) -> dict:
    response = client.post(
        "/api/v1/knowledge/upload",
        headers=headers,
        files={"file": (name, body, mime)},
        data=form,
    )
    assert response.status_code == 201, response.text
    return response.json()


LIPSTICK_TEXT = (
    "The Velvet Matte Lipstick collection features rich crimson and rose shades. "
    "Its long-wear formula keeps lips hydrated for twelve hours. " * 10
).encode()

SERUM_TEXT = (
    "Aurora Serum contains niacinamide and hyaluronic acid for skin hydration. "
    "Apply two drops of serum to the face every morning before sunscreen. " * 10
).encode()


# --------------------------------------------------------------------------- #
# Embedding job lifecycle
# --------------------------------------------------------------------------- #
def test_upload_triggers_embedding_job(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload(client, headers, "lipstick.txt", LIPSTICK_TEXT, "text/plain")
    # Response is produced before the background job runs
    assert doc["embedding_status"] == "pending"

    refreshed = client.get(f"/api/v1/knowledge/{doc['id']}", headers=headers).json()
    assert refreshed["embedding_status"] == "completed"
    assert refreshed["vector_count"] == refreshed["chunk_count"] > 0
    assert refreshed["embedding_model"] == "hashing"
    assert refreshed["embedded_at"] is not None


def test_replace_reembeds_document(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload(client, headers, "lipstick.txt", LIPSTICK_TEXT, "text/plain")

    response = client.post(
        f"/api/v1/knowledge/{doc['id']}/replace",
        headers=headers,
        files={"file": ("serum.txt", SERUM_TEXT, "text/plain")},
    )
    assert response.status_code == 200, response.text

    refreshed = client.get(f"/api/v1/knowledge/{doc['id']}", headers=headers).json()
    assert refreshed["embedding_status"] == "completed"
    assert refreshed["vector_count"] == refreshed["chunk_count"]

    stats = client.get("/api/v1/knowledge/index/stats", headers=headers).json()
    # Old version's vectors were replaced, not accumulated
    assert stats["vector_count"] == refreshed["chunk_count"]


def test_reindex_reembeds_document(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload(client, headers, "serum.txt", SERUM_TEXT, "text/plain")
    response = client.post(f"/api/v1/knowledge/{doc['id']}/reindex", headers=headers)
    assert response.status_code == 200
    refreshed = client.get(f"/api/v1/knowledge/{doc['id']}", headers=headers).json()
    assert refreshed["embedding_status"] == "completed"
    assert refreshed["vector_count"] > 0


def test_embedding_retry_then_success(client: TestClient, seed_roles, monkeypatch) -> None:
    """A provider that fails twice then succeeds should still complete."""
    from app.ai.embeddings import get_embedding_provider

    provider = get_embedding_provider()
    original = provider.embed_texts
    calls = {"n": 0}

    def flaky(texts):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise ConnectionError("transient embedding failure")
        return original(texts)

    monkeypatch.setattr(provider, "embed_texts", flaky)

    headers = _auth_headers(client)
    doc = _upload(client, headers, "flaky.txt", b"retry me please " * 50, "text/plain")
    refreshed = client.get(f"/api/v1/knowledge/{doc['id']}", headers=headers).json()
    assert calls["n"] >= 3
    assert refreshed["embedding_status"] == "completed"


def test_embedding_failure_marks_document_failed(client: TestClient, seed_roles, monkeypatch) -> None:
    from app.ai.embeddings import get_embedding_provider

    provider = get_embedding_provider()

    def always_fail(texts):
        raise ConnectionError("embedding backend down")

    monkeypatch.setattr(provider, "embed_texts", always_fail)

    headers = _auth_headers(client)
    doc = _upload(client, headers, "doomed.txt", b"this will fail " * 50, "text/plain")
    refreshed = client.get(f"/api/v1/knowledge/{doc['id']}", headers=headers).json()
    assert refreshed["embedding_status"] == "failed"
    assert "embedding backend down" in refreshed["embedding_error"]
    assert refreshed["vector_count"] == 0


# --------------------------------------------------------------------------- #
# Semantic search
# --------------------------------------------------------------------------- #
def test_search_returns_relevant_chunk_with_score(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    _upload(client, headers, "lipstick.txt", LIPSTICK_TEXT, "text/plain", brand="NUMÉ")
    serum = _upload(client, headers, "serum.txt", SERUM_TEXT, "text/plain", brand="NUMÉ")

    response = client.post(
        "/api/v1/knowledge/search",
        headers=headers,
        json={"query": "niacinamide hyaluronic acid serum hydration", "top_k": 3},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] > 0
    assert body["took_ms"] >= 0
    top = body["results"][0]
    # Hashing embeddings match on shared tokens — serum doc must win
    assert top["document_id"] == serum["id"]
    assert "serum" in top["content"].lower()
    assert 0 < top["score"] <= 1.0
    assert top["chunk_id"]
    assert top["title"] == serum["title"]


def test_search_respects_top_k_and_filters(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    lipstick = _upload(
        client, headers, "lipstick.txt", LIPSTICK_TEXT, "text/plain", brand="NUMÉ"
    )
    _upload(client, headers, "serum.txt", SERUM_TEXT, "text/plain", brand="OtherBrand")

    # top_k
    response = client.post(
        "/api/v1/knowledge/search",
        headers=headers,
        json={"query": "lipstick serum", "top_k": 1},
    )
    assert len(response.json()["results"]) == 1

    # brand filter
    response = client.post(
        "/api/v1/knowledge/search",
        headers=headers,
        json={"query": "hydration formula", "top_k": 10, "brand": "NUMÉ"},
    )
    results = response.json()["results"]
    assert results and all(r["brand"] == "NUMÉ" for r in results)

    # document filter
    response = client.post(
        "/api/v1/knowledge/search",
        headers=headers,
        json={"query": "hydration formula", "top_k": 10, "document_id": lipstick["id"]},
    )
    results = response.json()["results"]
    assert results and all(r["document_id"] == lipstick["id"] for r in results)

    # category filter narrows to the auto-assigned category of the serum doc
    serum_doc = client.get("/api/v1/knowledge?search=serum", headers=headers).json()["items"][0]
    response = client.post(
        "/api/v1/knowledge/search",
        headers=headers,
        json={"query": "hydration formula", "top_k": 10, "category_id": serum_doc["category_id"]},
    )
    results = response.json()["results"]
    assert results and all(r["category_id"] == serum_doc["category_id"] for r in results)


def test_search_requires_auth(client: TestClient, seed_roles) -> None:
    response = client.post("/api/v1/knowledge/search", json={"query": "anything"})
    assert response.status_code == 401


def test_search_empty_index_returns_no_results(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    response = client.post(
        "/api/v1/knowledge/search", headers=headers, json={"query": "nothing indexed yet"}
    )
    assert response.status_code == 200
    assert response.json()["results"] == []


# --------------------------------------------------------------------------- #
# Index management
# --------------------------------------------------------------------------- #
def test_index_stats(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload(client, headers, "lipstick.txt", LIPSTICK_TEXT, "text/plain")

    stats = client.get("/api/v1/knowledge/index/stats", headers=headers).json()
    assert stats["collection"] == get_settings().qdrant_collection
    assert stats["vector_count"] == doc["chunk_count"]
    assert stats["chunk_count"] == doc["chunk_count"]
    assert stats["documents_by_status"].get("completed") == 1
    assert stats["embedding_model"] == "hashing"
    assert stats["embedding_dimension"] == 384


def test_delete_index_resets_everything(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload(client, headers, "lipstick.txt", LIPSTICK_TEXT, "text/plain")

    response = client.delete("/api/v1/knowledge/index", headers=headers)
    assert response.status_code == 200

    stats = client.get("/api/v1/knowledge/index/stats", headers=headers).json()
    assert stats["vector_count"] == 0

    refreshed = client.get(f"/api/v1/knowledge/{doc['id']}", headers=headers).json()
    assert refreshed["embedding_status"] == "none"
    assert refreshed["vector_count"] == 0
    # Chunks in PostgreSQL are untouched — only vectors were dropped
    assert refreshed["chunk_count"] > 0

    # Re-index restores the vectors
    client.post(f"/api/v1/knowledge/{doc['id']}/reindex", headers=headers)
    stats = client.get("/api/v1/knowledge/index/stats", headers=headers).json()
    assert stats["vector_count"] > 0


def test_delete_document_removes_vectors(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    doc = _upload(client, headers, "lipstick.txt", LIPSTICK_TEXT, "text/plain")

    stats = client.get("/api/v1/knowledge/index/stats", headers=headers).json()
    assert stats["vector_count"] > 0

    client.delete(f"/api/v1/knowledge/{doc['id']}", headers=headers)
    stats = client.get("/api/v1/knowledge/index/stats", headers=headers).json()
    assert stats["vector_count"] == 0


# --------------------------------------------------------------------------- #
# Page numbers in payload
# --------------------------------------------------------------------------- #
def test_pdf_chunks_carry_page_numbers(client: TestClient, seed_roles) -> None:
    from tests.test_knowledge_ingestion import make_pdf

    headers = _auth_headers(client)
    doc = _upload(client, headers, "guide.pdf", make_pdf("NUME brand palette rules"), "application/pdf")

    chunks = client.get(f"/api/v1/knowledge/{doc['id']}/chunks", headers=headers).json()
    assert chunks["items"][0]["chunk_metadata"] == {"page": 1}

    response = client.post(
        "/api/v1/knowledge/search",
        headers=headers,
        json={"query": "brand palette rules", "top_k": 1},
    )
    top = response.json()["results"][0]
    assert top["page"] == 1
