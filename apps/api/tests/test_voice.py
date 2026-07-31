import io

import pytest

from app.core.config import get_settings
from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def test_transcribe_without_api_key_returns_501(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()

    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("audio.webm", io.BytesIO(b"not-real-audio-bytes"), "audio/webm")},
        headers=headers,
    )
    assert resp.status_code == 501

    get_settings.cache_clear()


async def test_speak_without_api_key_returns_501(client, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    get_settings.cache_clear()

    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/api/v1/voice/speak", json={"text": "Hallo Z"}, headers=headers)
    assert resp.status_code == 501

    get_settings.cache_clear()


async def test_transcribe_requires_auth(client):
    resp = await client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("audio.webm", io.BytesIO(b"x"), "audio/webm")},
    )
    assert resp.status_code == 401


async def test_speak_requires_auth(client):
    resp = await client.post("/api/v1/voice/speak", json={"text": "Hallo"})
    assert resp.status_code == 401
