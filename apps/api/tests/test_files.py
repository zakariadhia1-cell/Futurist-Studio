import io

import pytest

from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def test_files_require_auth(client):
    assert (await client.get("/api/v1/files")).status_code == 401
    assert (await client.post("/api/v1/files", files={"upload": ("a.txt", io.BytesIO(b"hi"))})).status_code == 401


async def test_upload_list_download_delete_roundtrip(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/v1/files",
        files={"upload": ("notiz.txt", io.BytesIO(b"Hallo Z"), "text/plain")},
        headers=headers,
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["filename"] == "notiz.txt"
    assert body["size_bytes"] == 7
    file_id = body["id"]

    listing = await client.get("/api/v1/files", headers=headers)
    assert listing.status_code == 200
    assert [f["id"] for f in listing.json()] == [file_id]

    download = await client.get(f"/api/v1/files/{file_id}/download", headers=headers)
    assert download.status_code == 200
    assert download.content == b"Hallo Z"

    delete = await client.delete(f"/api/v1/files/{file_id}", headers=headers)
    assert delete.status_code == 204

    listing_after = await client.get("/api/v1/files", headers=headers)
    assert listing_after.json() == []

    download_after = await client.get(f"/api/v1/files/{file_id}/download", headers=headers)
    assert download_after.status_code == 404


async def test_upload_rejects_empty_file(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/files", files={"upload": ("empty.txt", io.BytesIO(b""))}, headers=headers
    )
    assert resp.status_code == 400


async def test_files_are_isolated_per_user(client):
    token_a = await register_and_login(client, email="a@futurist.os")
    upload = await client.post(
        "/api/v1/files",
        files={"upload": ("secret.txt", io.BytesIO(b"top secret"))},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    file_id = upload.json()["id"]

    token_b = await register_and_login(client, email="b@futurist.os")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    assert (await client.get("/api/v1/files", headers=headers_b)).json() == []
    assert (await client.get(f"/api/v1/files/{file_id}/download", headers=headers_b)).status_code == 404
    assert (await client.delete(f"/api/v1/files/{file_id}", headers=headers_b)).status_code == 404
