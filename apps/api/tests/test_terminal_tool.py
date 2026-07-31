"""run_terminal_command had zero test coverage before this (see docs/AUDIT_REPORT.md,
Test Suite Honesty Check). Covers basic behavior plus F2 (docs/FIX_PLAN.md, S2): the
spawned shell must not inherit the API process's environment - a leaked JWT_SECRET_KEY/
DATABASE_URL/ENCRYPTION_KEY/provider API key would be a full secrets-exfiltration path."""
import uuid

import pytest

import app.orchestrator.tools  # noqa: F401 - registers built-in tools
from app.core.config import get_settings
from app.orchestrator.tool_registry import ToolContext, execute_tool

pytestmark = pytest.mark.asyncio


async def _get_user_id(client) -> uuid.UUID:
    from tests.conftest import register_and_login

    token = await register_and_login(client)
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return uuid.UUID(me.json()["id"])


async def test_run_terminal_command_executes_and_returns_output(client, db_session):
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool("run_terminal_command", {"command": "echo HALLO_FUTURIST"}, ctx)
    assert "Exit-Code 0" in result
    assert "HALLO_FUTURIST" in result


async def test_run_terminal_command_requires_a_command(client, db_session):
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool("run_terminal_command", {}, ctx)
    assert "Kein Befehl" in result


async def test_run_terminal_command_times_out(client, db_session):
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool("run_terminal_command", {"command": "sleep 30"}, ctx)
    assert "Zeitlimit" in result


async def test_run_terminal_command_does_not_leak_process_environment(client, db_session, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "totally-secret-jwt-key-do-not-leak")
    get_settings.cache_clear()
    try:
        user_id = await _get_user_id(client)
        ctx = ToolContext(db=db_session, user_id=user_id)
        result = await execute_tool("run_terminal_command", {"command": "env"}, ctx)
        assert "totally-secret-jwt-key-do-not-leak" not in result
        assert "JWT_SECRET_KEY" not in result
    finally:
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        get_settings.cache_clear()


async def test_run_terminal_command_still_has_a_usable_path(client, db_session):
    """A too-aggressive env strip (e.g. dropping PATH entirely) would break every
    command that isn't a full absolute path - this is what actually proves the
    allowlist in safe_shell_env() didn't overshoot."""
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool("run_terminal_command", {"command": "python3 --version"}, ctx)
    assert "Exit-Code 0" in result
