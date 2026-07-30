import pytest

from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def test_list_agents_requires_auth_and_returns_executive(client):
    unauthenticated = await client.get("/api/v1/agents")
    assert unauthenticated.status_code == 401

    token = await register_and_login(client)
    resp = await client.get("/api/v1/agents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    slugs = [a["slug"] for a in resp.json()]
    assert "executive" in slugs


async def test_create_and_list_conversation(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post("/api/v1/conversations", json={"title": "Erstes Gespraech"}, headers=headers)
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    listed = await client.get("/api/v1/conversations", headers=headers)
    assert listed.status_code == 200
    assert any(c["id"] == conversation_id for c in listed.json())


async def test_create_conversation_unknown_agent_404(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/api/v1/conversations", json={"agent_slug": "does-not-exist"}, headers=headers)
    assert resp.status_code == 404


async def test_messages_scoped_to_owner(client):
    token_a = await register_and_login(client, email="a@futurist.os")
    token_b = await register_and_login(client, email="b@futurist.os")

    created = await client.post(
        "/api/v1/conversations", json={"title": "A's Chat"}, headers={"Authorization": f"Bearer {token_a}"}
    )
    conversation_id = created.json()["id"]

    forbidden = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert forbidden.status_code == 404

    allowed = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert allowed.status_code == 200
    assert allowed.json() == []
