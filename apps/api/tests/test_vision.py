import io

import pytest

from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio

_TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001080600000"
    "01f15c4890000000a49444154789c6360000002000155a2d69a0000000049454e44ae426082"
)


async def test_analyze_image_requires_auth(client):
    resp = await client.post(
        "/api/v1/vision/analyze", files={"file": ("test.png", io.BytesIO(_TINY_PNG), "image/png")}
    )
    assert resp.status_code == 401


async def test_analyze_image_uses_fake_provider(client, monkeypatch):
    from app.models_provider import registry
    from app.models_provider.fake_provider import FakeProvider

    monkeypatch.setattr(registry, "get_provider", lambda provider: FakeProvider("Ein rotes Quadrat."))

    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/vision/analyze",
        files={"file": ("test.png", io.BytesIO(_TINY_PNG), "image/png")},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Ein rotes Quadrat."


async def test_ocr_uses_fake_provider(client, monkeypatch):
    from app.models_provider import registry
    from app.models_provider.fake_provider import FakeProvider

    monkeypatch.setattr(registry, "get_provider", lambda provider: FakeProvider("HALLO WELT"))

    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/vision/ocr",
        files={"file": ("test.png", io.BytesIO(_TINY_PNG), "image/png")},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["text"] == "HALLO WELT"


async def test_analyze_image_rejects_empty_file(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/vision/analyze", files={"file": ("empty.png", io.BytesIO(b""), "image/png")}, headers=headers
    )
    assert resp.status_code == 400
