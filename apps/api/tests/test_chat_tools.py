"""End-to-end: a tool-using agent's WebSocket turn actually executes its tool (against
the real DB) and returns the model's final answer - not just that the loop logic works
in isolation (see test_agent_runner.py), but that the WS handler wires it up correctly."""
import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models.agent import Agent
from app.models.model_config import ModelConfig
from app.models.task import Task
from app.models_provider import registry
from app.models_provider.base import ChatResult, ToolCall
from app.models_provider.fake_provider import ScriptedToolProvider
from tests.conftest import TestSessionLocal


def _seed_tool_agent() -> None:
    async def _seed() -> None:
        async with TestSessionLocal() as db:
            model_config = (
                await db.execute(select(ModelConfig).where(ModelConfig.is_default.is_(True)))
            ).scalar_one()
            db.add(
                Agent(
                    slug="developer",
                    name="Developer Agent",
                    system_prompt="Du bist ein Test-Developer-Agent.",
                    default_model_id=model_config.id,
                    config={"tools": ["create_task"]},
                )
            )
            await db.commit()

    asyncio.run(_seed())


def _count_tasks_titled(title: str) -> int:
    async def _count() -> int:
        async with TestSessionLocal() as db:
            result = await db.execute(select(Task).where(Task.title == title))
            return len(result.scalars().all())

    return asyncio.run(_count())


def _register_and_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "full_name": "Z"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    return login.json()["access_token"]


def test_chat_ws_executes_tool_call_and_persists_result(monkeypatch):
    _seed_tool_agent()

    script = [
        ChatResult(tool_calls=[ToolCall(id="c1", name="create_task", arguments={"title": "Testaufgabe"})]),
        ChatResult(text="Ich habe die Aufgabe 'Testaufgabe' fuer dich angelegt."),
    ]
    provider = ScriptedToolProvider(script)
    monkeypatch.setattr(registry, "get_provider", lambda p: provider)

    with TestClient(app) as client:
        token = _register_and_login(client, "toolws@futurist.os")
        headers = {"Authorization": f"Bearer {token}"}

        created = client.post(
            "/api/v1/conversations",
            json={"agent_slug": "developer", "title": "Tool-Test"},
            headers=headers,
        )
        assert created.status_code == 201
        conversation_id = created.json()["id"]

        with client.websocket_connect(f"/ws/chat/{conversation_id}?token={token}") as ws:
            ws.send_json({"type": "user_message", "content": "Leg eine Aufgabe 'Testaufgabe' an."})
            reply = ""
            while True:
                msg = ws.receive_json()
                if msg["type"] == "token":
                    reply += msg["payload"]["text"]
                elif msg["type"] == "done":
                    break
                elif msg["type"] == "error":
                    raise AssertionError(f"Unerwarteter Fehler: {msg}")

        assert "Testaufgabe" in reply
        assert provider.calls, "Provider wurde nie aufgerufen"

    assert _count_tasks_titled("Testaufgabe") == 1
