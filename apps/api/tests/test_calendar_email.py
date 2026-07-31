import uuid
from datetime import datetime, timedelta, timezone

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


async def test_calendar_tools_report_not_configured(client, db_session, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "")
    get_settings.cache_clear()

    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool("list_calendar_events", {}, ctx)
    assert "nicht konfiguriert" in result

    get_settings.cache_clear()


async def test_calendar_tools_report_not_connected(client, db_session, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "x")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "y")
    get_settings.cache_clear()

    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool("list_calendar_events", {}, ctx)
    assert "Kein Google-Konto verbunden" in result

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "")
    get_settings.cache_clear()


async def test_calendar_and_email_tools_with_connected_account(client, db_session, monkeypatch):
    from app.integrations import google_client
    from app.models.google_account import GoogleAccount

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "x")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "y")
    get_settings.cache_clear()

    user_id = await _get_user_id(client)

    account = GoogleAccount(
        user_id=user_id,
        google_email="z@gmail.com",
        access_token_encrypted="enc-access",
        refresh_token_encrypted="enc-refresh",
        token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scopes="",
    )
    db_session.add(account)
    await db_session.commit()

    async def fake_list_events(db, acc, *, max_results=10):
        return [{"summary": "Testtermin", "start": {"dateTime": "2026-08-01T10:00:00+02:00"}}]

    async def fake_create_event(db, acc, *, summary, start_iso, end_iso, description=None):
        return {"id": "evt1", "htmlLink": "https://calendar.google.com/event?eid=evt1"}

    async def fake_list_messages(db, acc, *, max_results=10):
        return [{"id": "m1", "from": "a@b.de", "subject": "Hallo", "date": "heute", "snippet": "Test-Snippet"}]

    async def fake_send_email(db, acc, *, to, subject, body):
        return {"id": "sent1"}

    monkeypatch.setattr(google_client, "list_calendar_events", fake_list_events)
    monkeypatch.setattr(google_client, "create_calendar_event", fake_create_event)
    monkeypatch.setattr(google_client, "list_recent_messages", fake_list_messages)
    monkeypatch.setattr(google_client, "send_email", fake_send_email)

    ctx = ToolContext(db=db_session, user_id=user_id)

    events_result = await execute_tool("list_calendar_events", {}, ctx)
    assert "Testtermin" in events_result

    create_result = await execute_tool(
        "create_calendar_event",
        {
            "summary": "Neuer Termin",
            "start_iso": "2026-08-01T10:00:00+02:00",
            "end_iso": "2026-08-01T11:00:00+02:00",
        },
        ctx,
    )
    assert "Neuer Termin" in create_result
    assert "evt1" in create_result

    missing_fields_result = await execute_tool("create_calendar_event", {"summary": "x"}, ctx)
    assert "erforderlich" in missing_fields_result

    emails_result = await execute_tool("list_recent_emails", {}, ctx)
    assert "Hallo" in emails_result
    assert "Test-Snippet" in emails_result

    send_result = await execute_tool(
        "send_email", {"to": "x@y.de", "subject": "Betreff", "body": "Inhalt"}, ctx
    )
    assert "x@y.de" in send_result

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "")
    get_settings.cache_clear()
