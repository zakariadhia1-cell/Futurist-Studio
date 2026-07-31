import pytest

pytestmark = pytest.mark.asyncio

CREDENTIALS = {"email": "z@futurist.os", "password": "supersecret123", "full_name": "Z"}


async def _register(client):
    return await client.post("/api/v1/auth/register", json=CREDENTIALS)


async def test_register_first_user_becomes_admin(client):
    resp = await _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["role"] == "admin"
    assert body["email"] == CREDENTIALS["email"]
    assert "hashed_password" not in body


async def test_register_duplicate_email_conflicts(client):
    await _register(client)
    resp = await _register(client)
    assert resp.status_code == 409


async def test_login_success_and_wrong_password(client):
    await _register(client)

    ok = await client.post(
        "/api/v1/auth/login", json={"email": CREDENTIALS["email"], "password": CREDENTIALS["password"]}
    )
    assert ok.status_code == 200
    assert "access_token" in ok.json()
    assert "refresh_token" in ok.json()

    bad = await client.post(
        "/api/v1/auth/login", json={"email": CREDENTIALS["email"], "password": "wrong-password"}
    )
    assert bad.status_code == 401


async def test_me_requires_valid_token(client):
    await _register(client)
    login = await client.post(
        "/api/v1/auth/login", json={"email": CREDENTIALS["email"], "password": CREDENTIALS["password"]}
    )
    access_token = login.json()["access_token"]

    ok = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert ok.status_code == 200
    assert ok.json()["email"] == CREDENTIALS["email"]

    unauthenticated = await client.get("/api/v1/auth/me")
    assert unauthenticated.status_code == 401


async def test_refresh_rotates_and_invalidates_old_token(client):
    await _register(client)
    login = await client.post(
        "/api/v1/auth/login", json={"email": CREDENTIALS["email"], "password": CREDENTIALS["password"]}
    )
    refresh_token = login.json()["refresh_token"]

    refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != refresh_token

    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reused.status_code == 401


async def test_logout_revokes_refresh_token(client):
    await _register(client)
    login = await client.post(
        "/api/v1/auth/login", json={"email": CREDENTIALS["email"], "password": CREDENTIALS["password"]}
    )
    refresh_token = login.json()["refresh_token"]

    logout = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 204

    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reused.status_code == 401
