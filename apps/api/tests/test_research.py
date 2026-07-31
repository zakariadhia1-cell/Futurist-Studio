"""research.py had zero test coverage before this (see docs/AUDIT_REPORT.md, Test Suite
Honesty Check) - and was also the tool with the SSRF hole (S4). Covers read_page's
rejection behavior; the actual redirect-safety mechanism is tested at the ssrf_guard
level in test_ssrf_guard.py (mocking httpx there, not here, is what lets those tests
simulate a multi-hop redirect chain without real network access)."""
import uuid

import pytest

import app.orchestrator.tools  # noqa: F401 - registers built-in tools
from app.orchestrator.tool_registry import ToolContext, execute_tool

pytestmark = pytest.mark.asyncio


async def _ctx(db_session) -> ToolContext:
    return ToolContext(db=db_session, user_id=uuid.uuid4())


async def test_read_page_requires_a_url(db_session):
    result = await execute_tool("read_page", {}, await _ctx(db_session))
    assert "Keine URL" in result


async def test_read_page_rejects_loopback_target(db_session):
    result = await execute_tool("read_page", {"url": "http://127.0.0.1:6379/"}, await _ctx(db_session))
    assert "abgelehnt" in result


async def test_read_page_rejects_cloud_metadata_endpoint(db_session):
    result = await execute_tool(
        "read_page", {"url": "http://169.254.169.254/latest/meta-data/"}, await _ctx(db_session)
    )
    assert "abgelehnt" in result


async def test_read_page_rejects_a_bare_hostname_that_resolves_to_loopback(db_session):
    """No scheme given - _read_page prepends https:// before validating; the SSRF guard
    still has to catch it, not just the literal http://127.0.0.1 form."""
    result = await execute_tool("read_page", {"url": "localhost"}, await _ctx(db_session))
    assert "abgelehnt" in result
