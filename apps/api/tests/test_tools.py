import uuid

import pytest
from sqlalchemy import select

import app.orchestrator.tools  # noqa: F401 - registers built-in tools
from app.models.agent import Agent
from app.models.model_config import ModelConfig
from app.models.task import Task
from app.models_provider.base import ChatResult
from app.models_provider.fake_provider import ScriptedToolProvider
from app.orchestrator.tool_registry import ToolContext, execute_tool
from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def _get_user_id(client) -> uuid.UUID:
    token = await register_and_login(client)
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return uuid.UUID(me.json()["id"])


async def test_create_task_tool_persists_a_task(client, db_session):
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)

    result = await execute_tool("create_task", {"title": "Rechnung schreiben", "priority": "high"}, ctx)
    assert "Rechnung schreiben" in result

    task = (await db_session.execute(select(Task).where(Task.user_id == user_id))).scalar_one()
    assert task.title == "Rechnung schreiben"
    assert task.priority == "high"


async def test_create_task_tool_rejects_unknown_project(client, db_session):
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)

    result = await execute_tool(
        "create_task", {"title": "X", "project_id": str(uuid.uuid4())}, ctx
    )
    assert "nicht gefunden" in result


async def test_read_write_file_tool_roundtrip(client, db_session, tmp_path, monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("WORKSPACES_DIR", str(tmp_path))
    get_settings.cache_clear()

    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)

    written = await execute_tool("write_file", {"path": "notes.txt", "content": "Hallo Workspace"}, ctx)
    assert "gespeichert" in written

    read_back = await execute_tool("read_file", {"path": "notes.txt"}, ctx)
    assert read_back == "Hallo Workspace"

    get_settings.cache_clear()


async def test_file_tool_rejects_path_traversal(client, db_session, tmp_path, monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("WORKSPACES_DIR", str(tmp_path))
    get_settings.cache_clear()

    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)

    result = await execute_tool("read_file", {"path": "../../../etc/passwd"}, ctx)
    assert "verlaesst" in result

    get_settings.cache_clear()


async def test_delegate_to_agent_invokes_target_agent(client, db_session, monkeypatch):
    user_id = await _get_user_id(client)

    model_config = (await db_session.execute(select(ModelConfig).where(ModelConfig.is_default.is_(True)))).scalar_one()
    target_agent = Agent(
        slug="research",
        name="Research Agent",
        system_prompt="Du bist ein Test-Research-Agent.",
        default_model_id=model_config.id,
        config={"tools": []},
    )
    db_session.add(target_agent)
    await db_session.commit()

    provider = ScriptedToolProvider([ChatResult(text="Ergebnis der Recherche.")])
    import app.models_provider.registry as registry

    monkeypatch.setattr(registry, "get_provider", lambda p: provider)

    ctx = ToolContext(db=db_session, user_id=user_id, conversation_id=None)
    result = await execute_tool("delegate_to_agent", {"agent_slug": "research", "task": "Finde XYZ"}, ctx)

    assert "Research Agent" in result
    assert "Ergebnis der Recherche." in result


async def test_delegate_to_agent_refuses_self_delegation(client, db_session):
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool("delegate_to_agent", {"agent_slug": "executive", "task": "..."}, ctx)
    assert "nicht" in result.lower()
