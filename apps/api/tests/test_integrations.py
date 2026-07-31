import uuid
from urllib.parse import parse_qs, urlparse

import pytest

from app.core.config import get_settings
from tests.conftest import TestSessionLocal, register_and_login

pytestmark = pytest.mark.asyncio


def _configure_google(monkeypatch, client_id="test-client-id", client_secret="test-client-secret"):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", client_id)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", client_secret)
    get_settings.cache_clear()


def _unconfigure_google(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "")
    get_settings.cache_clear()


async def _auth_headers(client) -> dict:
    token = await register_and_login(client)
    return {"Authorization": f"Bearer {token}"}


async def test_status_requires_auth(client):
    resp = await client.get("/api/v1/auth/google/status")
    assert resp.status_code == 401


async def test_status_reports_not_configured(client, monkeypatch):
    _unconfigure_google(monkeypatch)
    headers = await _auth_headers(client)
    resp = await client.get("/api/v1/auth/google/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"configured": False, "connected": False, "google_email": None}
    get_settings.cache_clear()


async def test_status_reports_configured_not_connected(client, monkeypatch):
    _configure_google(monkeypatch)
    headers = await _auth_headers(client)
    resp = await client.get("/api/v1/auth/google/status", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True
    assert body["connected"] is False
    get_settings.cache_clear()


async def test_connect_requires_configuration(client, monkeypatch):
    _unconfigure_google(monkeypatch)
    headers = await _auth_headers(client)
    resp = await client.get("/api/v1/auth/google/connect", headers=headers)
    assert resp.status_code == 503
    get_settings.cache_clear()


async def test_connect_returns_authorize_url_with_state(client, monkeypatch):
    _configure_google(monkeypatch)
    headers = await _auth_headers(client)
    resp = await client.get("/api/v1/auth/google/connect", headers=headers)
    assert resp.status_code == 200
    url = resp.json()["authorize_url"]
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=test-client-id" in url
    assert "state=" in url
    get_settings.cache_clear()


async def test_callback_rejects_missing_code(client):
    resp = await client.get("/api/v1/auth/google/callback", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "google=error" in resp.headers["location"]


async def test_callback_rejects_invalid_state(client):
    resp = await client.get(
        "/api/v1/auth/google/callback",
        params={"code": "abc", "state": "not-a-real-jwt"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 307)
    assert "google=error" in resp.headers["location"]


async def test_callback_success_stores_encrypted_tokens_and_status_reflects_it(client, monkeypatch):
    from cryptography.fernet import Fernet

    from app.core import crypto
    from app.integrations import google_oauth
    from app.models.google_account import GoogleAccount
    from sqlalchemy import select

    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    _configure_google(monkeypatch)
    crypto._get_fernet.cache_clear()

    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]

    connect_resp = await client.get("/api/v1/auth/google/connect", headers=headers)
    authorize_url = connect_resp.json()["authorize_url"]
    state = parse_qs(urlparse(authorize_url).query)["state"][0]

    async def fake_exchange_code(code):
        assert code == "test-auth-code"
        return {
            "access_token": "fake-access-token",
            "refresh_token": "fake-refresh-token",
            "expires_in": 3600,
            "scope": "openid email",
        }

    async def fake_get_userinfo(access_token):
        assert access_token == "fake-access-token"
        return {"email": "z@gmail.com"}

    monkeypatch.setattr(google_oauth, "exchange_code", fake_exchange_code)
    monkeypatch.setattr(google_oauth, "get_userinfo", fake_get_userinfo)

    callback_resp = await client.get(
        "/api/v1/auth/google/callback",
        params={"code": "test-auth-code", "state": state},
        follow_redirects=False,
    )
    assert callback_resp.status_code in (302, 307)
    assert "google=connected" in callback_resp.headers["location"]

    async with TestSessionLocal() as session:
        result = await session.execute(select(GoogleAccount).where(GoogleAccount.user_id == uuid.UUID(user_id)))
        account = result.scalar_one()
        assert account.google_email == "z@gmail.com"
        assert account.access_token_encrypted != "fake-access-token"
        assert crypto.decrypt(account.access_token_encrypted) == "fake-access-token"
        assert crypto.decrypt(account.refresh_token_encrypted) == "fake-refresh-token"

    status_resp = await client.get("/api/v1/auth/google/status", headers=headers)
    assert status_resp.json() == {"configured": True, "connected": True, "google_email": "z@gmail.com"}

    disconnect_resp = await client.delete("/api/v1/auth/google", headers=headers)
    assert disconnect_resp.status_code == 204

    status_after = await client.get("/api/v1/auth/google/status", headers=headers)
    assert status_after.json()["connected"] is False

    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    get_settings.cache_clear()
    crypto._get_fernet.cache_clear()
