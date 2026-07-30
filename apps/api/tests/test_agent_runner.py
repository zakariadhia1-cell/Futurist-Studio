import pytest
from sqlalchemy import select

import app.orchestrator.tools  # noqa: F401 - registers built-in tools
from app.models.agent import Agent
from app.models.message import Message
from app.models_provider.base import ChatResult, ToolCall
from app.models_provider.fake_provider import ScriptedToolProvider
from app.orchestrator.runner import MAX_TOOL_ITERATIONS, run_agent_turn
from app.orchestrator.tool_registry import ToolContext
from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def _get_user_id(client):
    token = await register_and_login(client)
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return me.json()["id"]


async def test_run_agent_turn_executes_tool_then_answers(client, db_session):
    user_id = await _get_user_id(client)
    agent = (await db_session.execute(select(Agent).where(Agent.slug == "executive"))).scalar_one()

    script = [
        ChatResult(tool_calls=[ToolCall(id="call_1", name="prioritize_projects", arguments={})]),
        ChatResult(text="Du hast aktuell keine aktiven Projekte."),
    ]
    provider = ScriptedToolProvider(script)
    history = [Message(conversation_id=None, role="user", content="Was sind meine Projekte?")]
    ctx = ToolContext(db=db_session, user_id=user_id, conversation_id=None)

    result = await run_agent_turn(
        agent, "anthropic", "claude-haiku-4-5-20251001", history, ctx, provider_factory=lambda p: provider
    )

    assert result == "Du hast aktuell keine aktiven Projekte."
    assert len(provider.calls) == 2
    # second call's history must include the tool's result as a "tool" message
    assert provider.calls[1][-1].role == "tool"
    assert "Keine aktiven Projekte" in provider.calls[1][-1].content


async def test_run_agent_turn_gives_up_after_max_iterations(client, db_session):
    user_id = await _get_user_id(client)
    agent = (await db_session.execute(select(Agent).where(Agent.slug == "executive"))).scalar_one()

    # Always returns a tool call, never a final text answer.
    script = [
        ChatResult(tool_calls=[ToolCall(id=f"call_{i}", name="prioritize_projects", arguments={})])
        for i in range(MAX_TOOL_ITERATIONS)
    ]
    provider = ScriptedToolProvider(script)
    history = [Message(conversation_id=None, role="user", content="Endlosschleife?")]
    ctx = ToolContext(db=db_session, user_id=user_id, conversation_id=None)

    result = await run_agent_turn(
        agent, "anthropic", "claude-haiku-4-5-20251001", history, ctx, provider_factory=lambda p: provider
    )

    assert "nicht" in result.lower()
    assert len(provider.calls) == MAX_TOOL_ITERATIONS
