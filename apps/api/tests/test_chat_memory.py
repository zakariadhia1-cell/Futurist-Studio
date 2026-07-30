"""Verifies Phase 2's core promise: the chat WebSocket retrieves relevant knowledge-base
content and folds it into the model call, so the agent 'remembers' ingested documents."""
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.main import app
from app.models_provider import registry
from app.models_provider.base import ChatMessage, ModelProvider
from app.models_provider.fake_embeddings import FakeEmbeddingProvider


class EchoSystemPromptProvider(ModelProvider):
    """Replies with its own system prompt, so the test can assert on what it received."""

    async def stream_chat(
        self, system_prompt: str, messages: list[ChatMessage], model: str
    ) -> AsyncIterator[str]:
        yield system_prompt


def _register_and_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "full_name": "Z"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    return login.json()["access_token"]


def test_chat_folds_relevant_document_into_system_prompt(monkeypatch):
    monkeypatch.setattr(registry, "get_embedding_provider", lambda: FakeEmbeddingProvider())
    monkeypatch.setattr(registry, "get_provider", lambda provider: EchoSystemPromptProvider())

    with TestClient(app) as client:
        token = _register_and_login(client, "memory@futurist.os")
        headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/api/v1/knowledge/documents",
            json={
                "title": "Lieblingswerkzeug",
                "content": "Z benutzt am liebsten Playwright fuer Browser-Automatisierung.",
            },
            headers=headers,
        )

        created = client.post("/api/v1/conversations", json={"title": "Memory-Test"}, headers=headers)
        conversation_id = created.json()["id"]

        with client.websocket_connect(f"/ws/chat/{conversation_id}?token={token}") as ws:
            ws.send_json({"type": "user_message", "content": "Welches Tool nutze ich fuer Browser-Automatisierung?"})

            echoed_prompt = ""
            while True:
                msg = ws.receive_json()
                if msg["type"] == "token":
                    echoed_prompt += msg["payload"]["text"]
                elif msg["type"] == "done":
                    break
                elif msg["type"] == "error":
                    raise AssertionError(f"Unerwarteter Fehler: {msg}")

        assert "Playwright" in echoed_prompt
        assert "Relevanter Kontext aus dem Gedaechtnis" in echoed_prompt


def test_chat_without_relevant_documents_has_no_memory_block(monkeypatch):
    monkeypatch.setattr(registry, "get_embedding_provider", lambda: FakeEmbeddingProvider())
    monkeypatch.setattr(registry, "get_provider", lambda provider: EchoSystemPromptProvider())

    with TestClient(app) as client:
        token = _register_and_login(client, "nomemory@futurist.os")
        headers = {"Authorization": f"Bearer {token}"}

        created = client.post("/api/v1/conversations", json={"title": "No-Memory-Test"}, headers=headers)
        conversation_id = created.json()["id"]

        with client.websocket_connect(f"/ws/chat/{conversation_id}?token={token}") as ws:
            ws.send_json({"type": "user_message", "content": "Hallo, wie geht's?"})

            echoed_prompt = ""
            while True:
                msg = ws.receive_json()
                if msg["type"] == "token":
                    echoed_prompt += msg["payload"]["text"]
                elif msg["type"] == "done":
                    break

        assert "Relevanter Kontext aus dem Gedaechtnis" not in echoed_prompt
