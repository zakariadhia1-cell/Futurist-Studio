"""All in one test function, deliberately: Playwright's async driver is bound to
whichever event loop first launches it, and starlette's TestClient spins up a *new*
event loop (an anyio portal thread) for every separate `with TestClient(app) as client`
block. Splitting this across multiple test functions caused exactly that - the browser
launched in test A's loop, then test B's TestClient loop tried to drive it and hung
forever with no error (found by actually running this, not by inspection)."""
import base64

import pytest
from fastapi.testclient import TestClient

from app.main import app

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

_TEST_PAGE = (
    "data:text/html,"
    "<html><body><h1>Testseite</h1>"
    '<input id="name" /><button onclick="document.title=document.getElementById(\'name\').value">Go</button>'
    "</body></html>"
)


def _register_and_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "full_name": "Z"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    return login.json()["access_token"]


def test_browser_session_lifecycle_and_actions():
    with TestClient(app) as client:
        token = _register_and_login(client, "browser1@futurist.os")
        headers = {"Authorization": f"Bearer {token}"}

        created = client.post("/api/v1/browser/sessions", headers=headers)
        assert created.status_code == 201
        session_id = created.json()["id"]

        listed = client.get("/api/v1/browser/sessions", headers=headers)
        assert session_id in listed.json()["sessions"]

        with client.websocket_connect(f"/ws/browser/{session_id}?token={token}") as ws:
            initial = ws.receive_json()
            assert initial["type"] == "screenshot"
            assert base64.b64decode(initial["payload"]["image_base64"])[:8] == _PNG_MAGIC

            ws.send_json({"type": "action", "action": "navigate", "args": {"url": _TEST_PAGE}})
            result = ws.receive_json()
            assert result["type"] == "result"
            assert "Navigiert" in result["payload"]["message"]
            screenshot = ws.receive_json()
            assert base64.b64decode(screenshot["payload"]["image_base64"])[:8] == _PNG_MAGIC

            ws.send_json({"type": "action", "action": "fill", "args": {"selector": "#name", "value": "Z"}})
            fill_result = ws.receive_json()
            assert fill_result["type"] == "result"
            ws.receive_json()  # screenshot

            ws.send_json({"type": "action", "action": "click", "args": {"selector": "button"}})
            click_result = ws.receive_json()
            assert click_result["type"] == "result"
            ws.receive_json()  # screenshot

            ws.send_json({"type": "action", "action": "unknown_action", "args": {}})
            unknown = ws.receive_json()
            assert unknown["type"] == "result"
            assert "Unbekannte Aktion" in unknown["payload"]["message"]

        closed = client.delete(f"/api/v1/browser/sessions/{session_id}", headers=headers)
        assert closed.status_code == 204
        listed_after = client.get("/api/v1/browser/sessions", headers=headers)
        assert session_id not in listed_after.json()["sessions"]


def test_browser_ws_rejects_other_users_session():
    with TestClient(app) as client:
        owner_token = _register_and_login(client, "browserowner@futurist.os")
        other_token = _register_and_login(client, "browserother@futurist.os")

        created = client.post(
            "/api/v1/browser/sessions", headers={"Authorization": f"Bearer {owner_token}"}
        )
        session_id = created.json()["id"]

        with pytest.raises(Exception):
            with client.websocket_connect(f"/ws/browser/{session_id}?token={other_token}") as ws:
                ws.receive_json()


def test_non_admin_member_cannot_create_browser_session():
    """F3 (docs/FIX_PLAN.md, S3 in docs/AUDIT_REPORT.md): only the admin gets a real
    headless-Chromium session - a self-registered member must not."""
    with TestClient(app) as client:
        _register_and_login(client, "browseradmin@futurist.os")  # first user, becomes admin
        member_token = _register_and_login(client, "browsermember@futurist.os")
        resp = client.post(
            "/api/v1/browser/sessions", headers={"Authorization": f"Bearer {member_token}"}
        )
        assert resp.status_code == 403
