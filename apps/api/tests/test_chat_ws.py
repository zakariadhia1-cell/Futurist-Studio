from fastapi.testclient import TestClient

from app.main import app
from app.models_provider import registry
from app.models_provider.fake_provider import FakeProvider


def _register_and_login(client: TestClient, email: str = "z@futurist.os") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "full_name": "Z"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    return login.json()["access_token"]


def test_chat_ws_streams_fake_reply(monkeypatch):
    monkeypatch.setattr(registry, "get_provider", lambda provider: FakeProvider("Hallo Z, alles klar."))

    with TestClient(app) as client:
        token = _register_and_login(client)
        created = client.post(
            "/api/v1/conversations",
            json={"title": "WS-Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        conversation_id = created.json()["id"]

        with client.websocket_connect(f"/ws/chat/{conversation_id}?token={token}") as ws:
            ws.send_json({"type": "user_message", "content": "Hallo!"})

            tokens = []
            while True:
                msg = ws.receive_json()
                if msg["type"] == "token":
                    tokens.append(msg["payload"]["text"])
                elif msg["type"] == "done":
                    break
                elif msg["type"] == "error":
                    raise AssertionError(f"Unerwarteter Fehler vom Server: {msg}")

            assert "".join(tokens).strip() == "Hallo Z, alles klar."

        messages = client.get(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        assert [m["role"] for m in messages] == ["user", "assistant"]
        assert messages[1]["content"].strip() == "Hallo Z, alles klar."


def test_chat_ws_rejects_missing_token():
    with TestClient(app) as client:
        created_token = _register_and_login(client, email="owner@futurist.os")
        created = client.post(
            "/api/v1/conversations",
            json={"title": "WS-Test"},
            headers={"Authorization": f"Bearer {created_token}"},
        )
        conversation_id = created.json()["id"]

        try:
            with client.websocket_connect(f"/ws/chat/{conversation_id}") as ws:
                ws.receive_text()
            raised = False
        except Exception:
            raised = True
        assert raised


def test_chat_ws_rejects_other_users_conversation():
    with TestClient(app) as client:
        owner_token = _register_and_login(client, email="owner2@futurist.os")
        other_token = _register_and_login(client, email="other2@futurist.os")

        created = client.post(
            "/api/v1/conversations",
            json={"title": "WS-Test"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        conversation_id = created.json()["id"]

        with client.websocket_connect(f"/ws/chat/{conversation_id}?token={other_token}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "error"
