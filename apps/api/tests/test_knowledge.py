import pytest

from app.models_provider import registry
from app.models_provider.fake_embeddings import FakeEmbeddingProvider
from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _fake_embeddings(monkeypatch):
    monkeypatch.setattr(registry, "get_embedding_provider", lambda: FakeEmbeddingProvider())


async def test_create_and_list_document(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/knowledge/documents",
        json={"title": "Python-Notizen", "content": "Python ist grossartig fuer Automatisierung."},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["content_text"] == "Python ist grossartig fuer Automatisierung."

    listed = await client.get("/api/v1/knowledge/documents", headers=headers)
    assert listed.status_code == 200
    assert any(d["title"] == "Python-Notizen" for d in listed.json())


async def test_search_ranks_relevant_document_first(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/knowledge/documents",
        json={
            "title": "Python Automatisierung",
            "content": "Python Skripte automatisieren repetitive Aufgaben effizient.",
        },
        headers=headers,
    )
    await client.post(
        "/api/v1/knowledge/documents",
        json={"title": "Kaffee Rezept", "content": "Kaffeebohnen roesten und mahlen fuer Espresso."},
        headers=headers,
    )

    resp = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "Wie automatisiere ich Aufgaben mit Python Skripten?"},
        headers=headers,
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results
    assert results[0]["document_title"] == "Python Automatisierung"


async def test_delete_document(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/knowledge/documents",
        json={"title": "Temp", "content": "Wird gleich geloescht."},
        headers=headers,
    )
    document_id = created.json()["id"]

    deleted = await client.delete(f"/api/v1/knowledge/documents/{document_id}", headers=headers)
    assert deleted.status_code == 204

    missing = await client.get(f"/api/v1/knowledge/documents/{document_id}", headers=headers)
    assert missing.status_code == 404


async def test_documents_scoped_to_owner(client):
    token_a = await register_and_login(client, email="owner-a@futurist.os")
    token_b = await register_and_login(client, email="owner-b@futurist.os")

    created = await client.post(
        "/api/v1/knowledge/documents",
        json={"title": "A's Geheimnis", "content": "Nur A soll das sehen."},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    document_id = created.json()["id"]

    forbidden = await client.get(
        f"/api/v1/knowledge/documents/{document_id}", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert forbidden.status_code == 404

    search_b = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "Geheimnis"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert search_b.json()["results"] == []
