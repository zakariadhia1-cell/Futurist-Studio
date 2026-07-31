import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_create_list_close_terminal_session(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post("/api/v1/terminal/sessions", headers=headers)
    assert created.status_code == 201
    session_id = created.json()["id"]

    listed = await client.get("/api/v1/terminal/sessions", headers=headers)
    assert session_id in listed.json()["sessions"]

    closed = await client.delete(f"/api/v1/terminal/sessions/{session_id}", headers=headers)
    assert closed.status_code == 204

    listed_after = await client.get("/api/v1/terminal/sessions", headers=headers)
    assert session_id not in listed_after.json()["sessions"]


@pytest.mark.asyncio
async def test_terminal_session_creation_is_rate_limited(client):
    """F3 (docs/FIX_PLAN.md, S3 in docs/AUDIT_REPORT.md): even the admin can't spin up
    unlimited real PTY sessions - the audit specifically called out zero rate limiting
    on this endpoint as a resource-exhaustion vector."""
    token = await register_and_login(client)  # first user, becomes admin
    headers = {"Authorization": f"Bearer {token}"}

    session_ids = []
    last_status = None
    try:
        for _ in range(21):
            resp = await client.post("/api/v1/terminal/sessions", headers=headers)
            last_status = resp.status_code
            if resp.status_code == 201:
                session_ids.append(resp.json()["id"])
    finally:
        for session_id in session_ids:
            await client.delete(f"/api/v1/terminal/sessions/{session_id}", headers=headers)

    assert last_status == 429


@pytest.mark.asyncio
async def test_non_admin_member_cannot_create_terminal_session(client):
    """F3 (docs/FIX_PLAN.md, S3 in docs/AUDIT_REPORT.md): only the admin gets a real
    shell - a self-registered member must not."""
    await register_and_login(client)  # first user in this fresh DB, becomes admin
    member_token = await register_and_login(client, email="term-member@futurist.os")
    resp = await client.post(
        "/api/v1/terminal/sessions", headers={"Authorization": f"Bearer {member_token}"}
    )
    assert resp.status_code == 403


def _register_and_login_sync(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "full_name": "Z"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    return login.json()["access_token"]


def test_terminal_ws_echo_roundtrip():
    with TestClient(app) as client:
        token = _register_and_login_sync(client, "term1@futurist.os")
        headers = {"Authorization": f"Bearer {token}"}

        created = client.post("/api/v1/terminal/sessions", headers=headers)
        session_id = created.json()["id"]

        with client.websocket_connect(f"/ws/terminal/{session_id}?token={token}") as ws:
            ws.send_json({"type": "input", "data": "echo HALLO_FUTURIST\n"})

            output = ""
            for _ in range(50):
                msg = ws.receive_json()
                if msg["type"] == "output":
                    output += msg["data"]
                    if "HALLO_FUTURIST" in output:
                        break

            assert "HALLO_FUTURIST" in output


def test_terminal_ws_does_not_leak_process_environment(monkeypatch):
    """F2 (docs/FIX_PLAN.md, S2 in docs/AUDIT_REPORT.md): the PTY shell must not inherit
    the API process's environment - previously {**os.environ, "TERM": ...}."""
    monkeypatch.setenv("SUPER_SECRET_TEST_VALUE", "do-not-leak-this-9f3a2b")
    with TestClient(app) as client:
        token = _register_and_login_sync(client, "termleak@futurist.os")
        headers = {"Authorization": f"Bearer {token}"}

        created = client.post("/api/v1/terminal/sessions", headers=headers)
        session_id = created.json()["id"]

        with client.websocket_connect(f"/ws/terminal/{session_id}?token={token}") as ws:
            ws.send_json({"type": "input", "data": "env; echo ENV_DUMP_DONE\n"})

            output = ""
            for _ in range(50):
                msg = ws.receive_json()
                if msg["type"] == "output":
                    output += msg["data"]
                    if "ENV_DUMP_DONE" in output:
                        break

            assert "ENV_DUMP_DONE" in output
            assert "do-not-leak-this-9f3a2b" not in output
            assert "SUPER_SECRET_TEST_VALUE" not in output


def test_terminal_ws_rejects_other_users_session():
    with TestClient(app) as client:
        owner_token = _register_and_login_sync(client, "termowner@futurist.os")
        other_token = _register_and_login_sync(client, "termother@futurist.os")

        created = client.post(
            "/api/v1/terminal/sessions", headers={"Authorization": f"Bearer {owner_token}"}
        )
        session_id = created.json()["id"]

        with pytest.raises(Exception):
            with client.websocket_connect(f"/ws/terminal/{session_id}?token={other_token}") as ws:
                ws.receive_json()
