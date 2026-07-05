"""Tests for Phase 2.3 — the RAG engine (retrieval, prompts, memory, admin)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config.settings import get_settings


@pytest.fixture(autouse=True)
def isolated_upload_dir(tmp_path, monkeypatch):
    """Point file storage at a temp dir so tests don't touch ./uploads."""
    monkeypatch.setattr(get_settings(), "upload_path", str(tmp_path))
    yield


def _auth_headers(client: TestClient, email: str = "rag@nume.ai", password: str = "Pass1234A") -> dict:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "RAG Tester"},
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def _upload(client: TestClient, headers: dict, name: str, body: bytes, mime: str = "text/plain", **form) -> dict:
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


def _query(client: TestClient, headers: dict, message: str, **extra) -> dict:
    response = client.post(
        "/api/v1/rag/query", headers=headers, json={"message": message, **extra}
    )
    assert response.status_code == 200, response.text
    return response.json()


# --------------------------------------------------------------------------- #
# Core RAG flow
# --------------------------------------------------------------------------- #
def test_query_returns_answer_with_context_and_debug(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    serum = _upload(client, headers, "serum.txt", SERUM_TEXT, brand="NUMÉ")
    _upload(client, headers, "lipstick.txt", LIPSTICK_TEXT, brand="NUMÉ")

    body = _query(client, headers, "What does Aurora Serum contain?")

    # Answer + conversation created
    assert body["answer"]
    assert body["conversation_id"]
    assert body["provider"] == "mock"

    # Retrieved chunks with similarity + rank scores and citations
    chunks = body["retrieved_chunks"]
    assert chunks and chunks[0]["document_id"] == serum["id"]
    assert 0 < chunks[0]["score"] <= 1.0
    assert chunks[0]["rank_score"] >= chunks[0]["score"]
    assert chunks[0]["citation"] == 1

    # Sources aggregate per document
    sources = body["sources"]
    assert sources[0]["document_id"] == serum["id"]
    assert 1 in sources[0]["citations"]
    assert sources[0]["best_score"] > 0

    # Final prompt (prompt debugger) contains grounding rules + context
    prompt = body["final_prompt"]
    assert "Never answer from outside the retrieved knowledge" in prompt["system"]
    assert "[1]" in prompt["system"]
    assert prompt["messages"][-1] == {
        "role": "user",
        "content": "What does Aurora Serum contain?",
    }

    # Usage + timings
    assert body["usage"]["input_tokens"] > 0
    assert body["usage"]["total_tokens"] == (
        body["usage"]["input_tokens"] + body["usage"]["output_tokens"]
    )
    assert body["timings"]["total_ms"] >= body["timings"]["llm_ms"]


def test_strict_grounding_short_circuits_on_empty_index(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    body = _query(client, headers, "What is the capital of France?")
    assert body["retrieved_chunks"] == []
    assert body["sources"] == []
    assert body["provider"] == "none"
    assert "couldn't find anything" in body["answer"]
    assert body["usage"]["total_tokens"] == 0


def test_allow_general_knowledge_calls_llm_without_context(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    body = _query(
        client, headers, "What is the capital of France?", allow_general_knowledge=True
    )
    assert body["provider"] == "mock"
    assert "may carefully use general knowledge" in body["final_prompt"]["system"]


def test_metadata_filters_restrict_retrieval(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    _upload(client, headers, "serum.txt", SERUM_TEXT, brand="OtherBrand")
    lipstick = _upload(client, headers, "lipstick.txt", LIPSTICK_TEXT, brand="NUMÉ")

    body = _query(client, headers, "hydration formula", brand="NUMÉ", top_k=10)
    assert body["retrieved_chunks"]
    assert all(c["brand"] == "NUMÉ" for c in body["retrieved_chunks"])
    assert all(s["document_id"] == lipstick["id"] for s in body["sources"])


def test_multi_document_retrieval_caps_chunks_per_document(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    _upload(client, headers, "serum.txt", SERUM_TEXT)
    _upload(client, headers, "lipstick.txt", LIPSTICK_TEXT)

    body = _query(client, headers, "hydration serum lipstick formula", top_k=10)
    per_doc: dict[str, int] = {}
    for chunk in body["retrieved_chunks"]:
        per_doc[chunk["document_id"]] = per_doc.get(chunk["document_id"], 0) + 1
    cap = get_settings().rag_max_chunks_per_document
    assert per_doc and all(count <= cap for count in per_doc.values())


def test_priority_boost_for_brand_guideline_category(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    category = client.post(
        "/api/v1/knowledge/categories",
        headers=headers,
        json={"name": "Brand Guidelines"},
    ).json()
    doc = _upload(
        client, headers, "voice.txt", SERUM_TEXT, category_id=category["id"]
    )
    body = _query(client, headers, "serum hydration")
    boosted = [c for c in body["retrieved_chunks"] if c["document_id"] == doc["id"]]
    assert boosted and all(c["priority"] for c in boosted)
    assert boosted[0]["rank_score"] == pytest.approx(
        boosted[0]["score"] + get_settings().rag_priority_boost, abs=1e-3
    )


# --------------------------------------------------------------------------- #
# Conversation memory
# --------------------------------------------------------------------------- #
def test_conversation_memory_flows_into_prompt(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    _upload(client, headers, "serum.txt", SERUM_TEXT)

    first = _query(client, headers, "What does Aurora Serum contain?")
    conversation_id = first["conversation_id"]

    second = _query(
        client, headers, "How do I apply it?", conversation_id=conversation_id
    )
    assert second["conversation_id"] == conversation_id
    # History (user + assistant from turn 1) precedes the new question
    roles = [m["role"] for m in second["final_prompt"]["messages"]]
    assert roles == ["user", "assistant", "user"]

    conversation = client.get(
        f"/api/v1/rag/conversations/{conversation_id}", headers=headers
    ).json()
    assert conversation["message_count"] == 4
    assert conversation["total_output_tokens"] > 0

    messages = client.get(
        f"/api/v1/rag/conversations/{conversation_id}/messages", headers=headers
    ).json()
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]
    assert messages[1]["sources"]


def test_query_with_unknown_conversation_404s(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    response = client.post(
        "/api/v1/rag/query",
        headers=headers,
        json={
            "message": "hello",
            "conversation_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert response.status_code == 404


def test_conversation_crud(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    created = client.post(
        "/api/v1/rag/conversations", headers=headers, json={"title": "Campaign chat"}
    )
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    listed = client.get("/api/v1/rag/conversations", headers=headers).json()
    assert listed["total"] == 1

    deleted = client.delete(
        f"/api/v1/rag/conversations/{conversation_id}", headers=headers
    )
    assert deleted.status_code == 200
    assert (
        client.get(f"/api/v1/rag/conversations/{conversation_id}", headers=headers).status_code
        == 404
    )


# --------------------------------------------------------------------------- #
# Admin — debug, stats, config
# --------------------------------------------------------------------------- #
def test_message_debug_endpoint_returns_full_payload(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    _upload(client, headers, "serum.txt", SERUM_TEXT)
    body = _query(client, headers, "Tell me about the serum")

    debug = client.get(
        f"/api/v1/rag/messages/{body['message_id']}/debug", headers=headers
    ).json()
    assert debug["role"] == "assistant"
    assert debug["retrieved_chunks"]
    assert debug["final_prompt"]["system"]
    assert debug["rag_metadata"]["history_messages"] == 0
    assert debug["input_tokens"] > 0
    assert debug["total_ms"] is not None


def test_stats_aggregate_usage(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    _upload(client, headers, "serum.txt", SERUM_TEXT)
    _query(client, headers, "serum question one")
    _query(client, headers, "serum question two")

    stats = client.get("/api/v1/rag/stats", headers=headers).json()
    assert stats["query_count"] == 2
    assert stats["conversation_count"] == 2
    assert stats["total_tokens"] == stats["total_input_tokens"] + stats["total_output_tokens"]
    assert stats["avg_total_ms"] is not None
    assert stats["by_model"][0]["provider"] == "mock"
    assert stats["by_model"][0]["queries"] == 2


def test_config_endpoint(client: TestClient, seed_roles) -> None:
    headers = _auth_headers(client)
    config = client.get("/api/v1/rag/config", headers=headers).json()
    assert config["llm_provider"] == "mock"
    assert config["llm_configured"] is True
    assert config["top_k"] == get_settings().rag_top_k


def test_rag_endpoints_require_auth(client: TestClient, seed_roles) -> None:
    assert client.post("/api/v1/rag/query", json={"message": "hi"}).status_code == 401
    assert client.get("/api/v1/rag/conversations").status_code == 401
    assert client.get("/api/v1/rag/stats").status_code == 401
