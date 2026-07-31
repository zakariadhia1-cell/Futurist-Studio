"""GET /api/v1/dashboard/summary aggregates agent usage, token/cost estimates,
task/project counts, MCP-server counts and live-session counts into one response -
covers the empty-state shape and that real activity (conversations/messages, tasks,
projects, MCP servers, a terminal session) actually shows up in the right buckets."""
import uuid

import pytest
from sqlalchemy import select

from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def test_dashboard_summary_requires_auth(client):
    resp = await client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 401


async def test_dashboard_summary_empty_state(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["agents"] == [
        {"slug": "executive", "name": "Executive Agent", "conversation_count": 0, "message_count": 0}
    ]
    assert body["usage"] == {
        "total_tokens": 0,
        "total_messages": 0,
        "estimated_cost_usd": 0.0,
        "by_model": [],
        "daily": [],
    }
    assert body["tasks"] == {"todo": 0, "in_progress": 0, "done": 0, "overdue": 0, "total": 0}
    assert body["projects"] == {"active": 0, "paused": 0, "done": 0, "archived": 0, "total": 0}
    assert body["mcp_servers"] == {"total": 0, "enabled": 0}
    assert body["sessions"] == {"terminal_active": 0, "browser_active": 0}


async def test_dashboard_summary_reflects_real_activity(client, db_session):
    token = await register_and_login(client)  # first user in a fresh DB -> admin
    headers = {"Authorization": f"Bearer {token}"}
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me.json()["id"])

    await client.post("/api/v1/projects", json={"name": "Testprojekt"}, headers=headers)
    await client.post("/api/v1/tasks", json={"title": "Erledigen"}, headers=headers)
    task2 = await client.post("/api/v1/tasks", json={"title": "Fertig"}, headers=headers)
    await client.patch(f"/api/v1/tasks/{task2.json()['id']}", json={"status": "done"}, headers=headers)

    await client.post(
        "/api/v1/mcp/servers",
        json={"name": "echo", "transport": "stdio", "command": "echo", "args": ["hi"]},
        headers=headers,
    )

    from app.models.agent import Agent
    from app.models.conversation import Conversation
    from app.models.message import Message

    agent = (await db_session.execute(select(Agent).where(Agent.slug == "executive"))).scalar_one()
    conversation = Conversation(user_id=user_id, agent_id=agent.id, title="Test")
    db_session.add(conversation)
    await db_session.flush()
    db_session.add_all(
        [
            Message(
                conversation_id=conversation.id,
                role="user",
                content="Hallo",
                model_used="claude-haiku-4-5-20251001",
                tokens_used=10,
            ),
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content="Hallo zurueck",
                model_used="claude-haiku-4-5-20251001",
                tokens_used=25,
            ),
        ]
    )
    await db_session.commit()

    terminal_created = await client.post("/api/v1/terminal/sessions", headers=headers)
    assert terminal_created.status_code == 201

    resp = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["agents"] == [
        {"slug": "executive", "name": "Executive Agent", "conversation_count": 1, "message_count": 2}
    ]
    assert body["usage"]["total_tokens"] == 35
    assert body["usage"]["total_messages"] == 2
    assert body["usage"]["by_model"] == [
        {"model_name": "claude-haiku-4-5-20251001", "tokens": 35, "estimated_cost_usd": 0.0}
    ]
    assert len(body["usage"]["daily"]) == 1
    assert body["usage"]["daily"][0]["tokens"] == 35

    assert body["tasks"] == {"todo": 1, "in_progress": 0, "done": 1, "overdue": 0, "total": 2}
    assert body["projects"] == {"active": 1, "paused": 0, "done": 0, "archived": 0, "total": 1}
    assert body["mcp_servers"] == {"total": 1, "enabled": 1}
    assert body["sessions"] == {"terminal_active": 1, "browser_active": 0}

    await client.delete(f"/api/v1/terminal/sessions/{terminal_created.json()['id']}", headers=headers)


async def test_dashboard_summary_estimates_cost_from_model_config(client, db_session):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me.json()["id"])

    from app.models.agent import Agent
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.model_config import ModelConfig

    priced_model = ModelConfig(
        provider="openai",
        model_name="gpt-priced-test",
        display_name="GPT Priced Test",
        capabilities={},
        cost_per_1k_input=1.0,
        cost_per_1k_output=3.0,
    )
    db_session.add(priced_model)
    agent = (await db_session.execute(select(Agent).where(Agent.slug == "executive"))).scalar_one()
    conversation = Conversation(user_id=user_id, agent_id=agent.id, title="Kosten-Test")
    db_session.add(conversation)
    await db_session.flush()
    db_session.add(
        Message(
            conversation_id=conversation.id,
            role="assistant",
            content="Antwort",
            model_used="gpt-priced-test",
            tokens_used=1000,
        )
    )
    await db_session.commit()

    resp = await client.get("/api/v1/dashboard/summary", headers=headers)
    body = resp.json()
    # avg(1.0, 3.0) = 2.0 USD per 1k tokens * 1000 tokens / 1000 = 2.0
    assert body["usage"]["by_model"] == [
        {"model_name": "gpt-priced-test", "tokens": 1000, "estimated_cost_usd": 2.0}
    ]
    assert body["usage"]["estimated_cost_usd"] == 2.0
