"""Calendar/Gmail tools for the Executive Agent. All calls go live to Google (see
app/integrations/google_client.py for why there's no local sync/cache)."""
from sqlalchemy import select

from app.integrations import google_client, google_oauth
from app.models.google_account import GoogleAccount
from app.orchestrator.tool_registry import Tool, ToolContext, register

_NOT_CONFIGURED = "Google-Integration ist nicht konfiguriert (GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET fehlen)."
_NOT_CONNECTED = "Kein Google-Konto verbunden. In den Einstellungen unter 'Google-Konto' verbinden."


async def _get_connected_account(ctx: ToolContext) -> GoogleAccount | str:
    if not google_oauth.is_configured():
        return _NOT_CONFIGURED
    result = await ctx.db.execute(select(GoogleAccount).where(GoogleAccount.user_id == ctx.user_id))
    account = result.scalar_one_or_none()
    return account if account is not None else _NOT_CONNECTED


async def _list_calendar_events(arguments: dict, ctx: ToolContext) -> str:
    account = await _get_connected_account(ctx)
    if isinstance(account, str):
        return account

    max_results = int(arguments.get("max_results") or 10)
    try:
        events = await google_client.list_calendar_events(ctx.db, account, max_results=max_results)
    except Exception as exc:
        return f"Kalendertermine konnten nicht geladen werden: {exc}"

    if not events:
        return "Keine anstehenden Termine gefunden."
    lines = []
    for e in events:
        start = e.get("start", {}).get("dateTime") or e.get("start", {}).get("date", "?")
        lines.append(f"- {e.get('summary', '(ohne Titel)')} ({start})")
    return "Anstehende Termine:\n" + "\n".join(lines)


async def _create_calendar_event(arguments: dict, ctx: ToolContext) -> str:
    account = await _get_connected_account(ctx)
    if isinstance(account, str):
        return account

    summary = str(arguments.get("summary", "")).strip()
    start_iso = str(arguments.get("start_iso", "")).strip()
    end_iso = str(arguments.get("end_iso", "")).strip()
    if not summary or not start_iso or not end_iso:
        return "summary, start_iso und end_iso sind erforderlich (ISO-8601, z.B. 2026-08-01T14:00:00+02:00)."

    try:
        event = await google_client.create_calendar_event(
            ctx.db,
            account,
            summary=summary,
            start_iso=start_iso,
            end_iso=end_iso,
            description=arguments.get("description"),
        )
    except Exception as exc:
        return f"Termin konnte nicht angelegt werden: {exc}"
    return f"Termin '{summary}' angelegt: {event.get('htmlLink', event.get('id', ''))}"


async def _list_recent_emails(arguments: dict, ctx: ToolContext) -> str:
    account = await _get_connected_account(ctx)
    if isinstance(account, str):
        return account

    max_results = int(arguments.get("max_results") or 10)
    try:
        messages = await google_client.list_recent_messages(ctx.db, account, max_results=max_results)
    except Exception as exc:
        return f"E-Mails konnten nicht geladen werden: {exc}"

    if not messages:
        return "Kein E-Mails gefunden."
    lines = [f"- Von {m['from']}: '{m['subject']}' - {m['snippet']}" for m in messages]
    return "Letzte E-Mails:\n" + "\n".join(lines)


async def _send_email(arguments: dict, ctx: ToolContext) -> str:
    account = await _get_connected_account(ctx)
    if isinstance(account, str):
        return account

    to = str(arguments.get("to", "")).strip()
    subject = str(arguments.get("subject", "")).strip()
    body = str(arguments.get("body", ""))
    if not to or not subject:
        return "to und subject sind erforderlich."

    try:
        await google_client.send_email(ctx.db, account, to=to, subject=subject, body=body)
    except Exception as exc:
        return f"E-Mail konnte nicht gesendet werden: {exc}"
    return f"E-Mail an {to} gesendet: '{subject}'"


register(
    Tool(
        name="list_calendar_events",
        description="Listet die naechsten anstehenden Termine im Google-Kalender des Nutzers auf.",
        input_schema={
            "type": "object",
            "properties": {"max_results": {"type": "integer", "description": "Standard: 10"}},
        },
        handler=_list_calendar_events,
    )
)

register(
    Tool(
        name="create_calendar_event",
        description="Legt einen neuen Termin im Google-Kalender des Nutzers an.",
        input_schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "start_iso": {"type": "string", "description": "ISO-8601, z.B. 2026-08-01T14:00:00+02:00"},
                "end_iso": {"type": "string", "description": "ISO-8601"},
                "description": {"type": "string"},
            },
            "required": ["summary", "start_iso", "end_iso"],
        },
        handler=_create_calendar_event,
    )
)

register(
    Tool(
        name="list_recent_emails",
        description="Listet die neuesten E-Mails im Gmail-Posteingang des Nutzers auf (Absender, Betreff, Vorschau).",
        input_schema={
            "type": "object",
            "properties": {"max_results": {"type": "integer", "description": "Standard: 10"}},
        },
        handler=_list_recent_emails,
    )
)

register(
    Tool(
        name="send_email",
        description="Sendet eine E-Mail ueber das verbundene Gmail-Konto des Nutzers.",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
        handler=_send_email,
    )
)
