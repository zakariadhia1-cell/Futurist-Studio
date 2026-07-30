import pytest

from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def test_login_is_rate_limited_after_repeated_failures(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "rl@futurist.os", "password": "supersecret123", "full_name": "Z"},
    )

    last_status = None
    for _ in range(11):
        resp = await client.post(
            "/api/v1/auth/login", json={"email": "rl@futurist.os", "password": "wrong-password"}
        )
        last_status = resp.status_code

    assert last_status == 429


async def test_register_is_rate_limited_after_repeated_attempts(client):
    last_status = None
    for i in range(6):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": f"reg-rl-{i}@futurist.os", "password": "supersecret123", "full_name": "Z"},
        )
        last_status = resp.status_code

    assert last_status == 429


async def test_failed_login_is_audit_logged(client):
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "audit@futurist.os", "password": "supersecret123", "full_name": "Z"},
    )
    registered_user_id = register_resp.json()["id"]
    await client.post("/api/v1/auth/login", json={"email": "audit@futurist.os", "password": "wrong"})

    # The first registered user is always admin (see auth.py register()).
    admin_token = await register_and_login(client, email="audit@futurist.os")
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.get("/api/v1/audit-logs", headers=headers)
    assert resp.status_code == 200
    entries = resp.json()
    actions = [entry["action"] for entry in entries]
    assert "auth.login_failed" in actions
    assert "auth.register" in actions

    register_entry = next(e for e in entries if e["action"] == "auth.register")
    assert register_entry["user_id"] == registered_user_id


async def test_audit_logs_require_admin_role(client):
    await register_and_login(client, email="admin-first@futurist.os")
    member_token = await register_and_login(client, email="member-second@futurist.os")
    headers = {"Authorization": f"Bearer {member_token}"}
    resp = await client.get("/api/v1/audit-logs", headers=headers)
    assert resp.status_code == 403


async def test_audit_logs_require_auth(client):
    resp = await client.get("/api/v1/audit-logs")
    assert resp.status_code == 401
