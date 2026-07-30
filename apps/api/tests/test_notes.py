import pytest

from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def test_notes_require_auth(client):
    assert (await client.get("/api/v1/notes")).status_code == 401
    assert (await client.post("/api/v1/notes", json={"title": "x"})).status_code == 401


async def test_note_crud_roundtrip(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/notes", json={"title": "Ideen", "content": "FUTURIST OS weiterdenken"}, headers=headers
    )
    assert create.status_code == 201
    note_id = create.json()["id"]

    listing = await client.get("/api/v1/notes", headers=headers)
    assert listing.status_code == 200
    assert [n["id"] for n in listing.json()] == [note_id]

    update = await client.patch(
        f"/api/v1/notes/{note_id}", json={"content": "FUTURIST OS weiterdenken - Phase 7"}, headers=headers
    )
    assert update.status_code == 200
    assert update.json()["content"] == "FUTURIST OS weiterdenken - Phase 7"
    assert update.json()["title"] == "Ideen"

    delete = await client.delete(f"/api/v1/notes/{note_id}", headers=headers)
    assert delete.status_code == 204
    assert (await client.get("/api/v1/notes", headers=headers)).json() == []


async def test_notes_are_isolated_per_user(client):
    token_a = await register_and_login(client, email="a@futurist.os")
    create = await client.post(
        "/api/v1/notes",
        json={"title": "privat", "content": "geheim"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    note_id = create.json()["id"]

    token_b = await register_and_login(client, email="b@futurist.os")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    assert (await client.get("/api/v1/notes", headers=headers_b)).json() == []
    assert (await client.patch(f"/api/v1/notes/{note_id}", json={"title": "x"}, headers=headers_b)).status_code == 404
    assert (await client.delete(f"/api/v1/notes/{note_id}", headers=headers_b)).status_code == 404
