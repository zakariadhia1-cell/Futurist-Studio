import uuid

import pytest

import app.orchestrator.tools  # noqa: F401 - registers built-in tools
from app.core.config import get_settings
from app.orchestrator.tool_registry import ToolContext, execute_tool
from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def _get_user_id(client) -> uuid.UUID:
    token = await register_and_login(client)
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return uuid.UUID(me.json()["id"])


async def test_generate_image_without_api_key_gives_clear_message(client, db_session, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()

    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool("generate_image", {"prompt": "ein Logo fuer FUTURIST OS"}, ctx)

    assert "nicht konfiguriert" in result
    get_settings.cache_clear()


async def test_generate_invoice_pdf_creates_real_pdf(client, db_session, tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACES_DIR", str(tmp_path))
    get_settings.cache_clear()

    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)

    result = await execute_tool(
        "generate_invoice_pdf",
        {
            "client_name": "Musterkunde GmbH",
            "invoice_number": "RE-TEST-1",
            "items": [
                {"description": "Beratung", "quantity": 2, "unit_price": 150},
                {"description": "Umsetzung", "quantity": 1, "unit_price": 500},
            ],
        },
        ctx,
    )

    assert "RE-TEST-1" in result
    assert "800.00" in result  # 2*150 + 1*500

    pdf_path = tmp_path / str(user_id) / "invoices" / "RE-TEST-1.pdf"
    assert pdf_path.exists()
    assert pdf_path.read_bytes()[:4] == b"%PDF"

    get_settings.cache_clear()


async def test_generate_report_creates_real_pdf(client, db_session, tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACES_DIR", str(tmp_path))
    get_settings.cache_clear()

    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)

    result = await execute_tool(
        "generate_report", {"title": "Quartalsbericht", "content": "Alles laeuft gut.\n\nZweiter Absatz."}, ctx
    )

    assert "Quartalsbericht" in result
    reports_dir = tmp_path / str(user_id) / "reports"
    pdf_files = list(reports_dir.glob("*.pdf"))
    assert len(pdf_files) == 1
    assert pdf_files[0].read_bytes()[:4] == b"%PDF"

    get_settings.cache_clear()


async def test_seo_analyze_reports_unreachable_page(client, db_session):
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool(
        "seo_analyze", {"url": "http://this-domain-does-not-exist-futuristos-test.invalid"}, ctx
    )
    assert "konnte nicht geladen werden" in result


async def test_n8n_tools_report_not_configured(client, db_session, monkeypatch):
    monkeypatch.setenv("N8N_BASE_URL", "")
    monkeypatch.setenv("N8N_API_KEY", "")
    get_settings.cache_clear()

    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)

    list_result = await execute_tool("list_n8n_workflows", {}, ctx)
    assert "nicht konfiguriert" in list_result

    trigger_result = await execute_tool("trigger_n8n_workflow", {"webhook_path": "x"}, ctx)
    assert "nicht konfiguriert" in trigger_result

    get_settings.cache_clear()


async def test_call_api_rejects_private_target(client, db_session):
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool("call_api", {"url": "http://127.0.0.1:6379/"}, ctx)
    assert "abgelehnt" in result
