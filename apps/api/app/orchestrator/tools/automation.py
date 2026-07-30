"""Automation Agent: n8n workflow integration + a generic (SSRF-guarded) HTTP call tool."""
import json

import httpx

from app.core.config import get_settings
from app.orchestrator.tool_registry import Tool, ToolContext, register
from app.orchestrator.tools.ssrf_guard import is_safe_url

_MAX_RESPONSE_CHARS = 4_000


async def _list_n8n_workflows(arguments: dict, ctx: ToolContext) -> str:
    settings = get_settings()
    if not settings.N8N_BASE_URL or not settings.N8N_API_KEY:
        return "n8n ist nicht konfiguriert (N8N_BASE_URL/N8N_API_KEY fehlen in .env)."

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.N8N_BASE_URL.rstrip('/')}/api/v1/workflows",
                headers={"X-N8N-API-KEY": settings.N8N_API_KEY},
            )
            resp.raise_for_status()
    except Exception as exc:
        return f"n8n-Workflows konnten nicht geladen werden: {exc}"

    workflows = resp.json().get("data", [])
    if not workflows:
        return "Keine n8n-Workflows gefunden."
    lines = [f"- {w.get('name')} (id={w.get('id')}, aktiv={w.get('active')})" for w in workflows]
    return "n8n-Workflows:\n" + "\n".join(lines)


async def _trigger_n8n_workflow(arguments: dict, ctx: ToolContext) -> str:
    settings = get_settings()
    if not settings.N8N_BASE_URL:
        return "n8n ist nicht konfiguriert (N8N_BASE_URL fehlt in .env)."

    webhook_path = str(arguments.get("webhook_path", "")).strip().lstrip("/")
    if not webhook_path:
        return "Kein webhook_path angegeben (der Pfad des Webhook-Trigger-Knotens im n8n-Workflow)."
    payload = arguments.get("data") or {}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{settings.N8N_BASE_URL.rstrip('/')}/webhook/{webhook_path}", json=payload)
            resp.raise_for_status()
    except Exception as exc:
        return f"n8n-Workflow konnte nicht ausgeloest werden: {exc}"

    body = resp.text[:_MAX_RESPONSE_CHARS]
    return f"Workflow '{webhook_path}' ausgeloest (Status {resp.status_code}).\nAntwort: {body}"


async def _call_api(arguments: dict, ctx: ToolContext) -> str:
    url = str(arguments.get("url", "")).strip()
    method = str(arguments.get("method", "GET")).upper()
    if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        return f"Unbekannte HTTP-Methode: {method}"
    if not is_safe_url(url):
        return "URL abgelehnt: nur oeffentliche http(s)-Adressen sind erlaubt (keine internen/privaten Ziele)."

    body = arguments.get("body")
    headers = arguments.get("headers") or {}
    if not isinstance(headers, dict):
        headers = {}

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            resp = await client.request(
                method,
                url,
                json=body if isinstance(body, (dict, list)) else None,
                content=body if isinstance(body, str) else None,
                headers=headers,
            )
    except Exception as exc:
        return f"API-Aufruf fehlgeschlagen: {exc}"

    text = resp.text[:_MAX_RESPONSE_CHARS]
    try:
        text = json.dumps(resp.json(), ensure_ascii=False)[:_MAX_RESPONSE_CHARS]
    except ValueError:
        pass
    return f"Status {resp.status_code}\n{text}"


register(
    Tool(
        name="list_n8n_workflows",
        description="Listet alle Workflows in der konfigurierten n8n-Instanz auf.",
        input_schema={"type": "object", "properties": {}},
        handler=_list_n8n_workflows,
    )
)

register(
    Tool(
        name="trigger_n8n_workflow",
        description=(
            "Loest einen n8n-Workflow ueber dessen Webhook-Pfad aus (der Workflow muss einen "
            "Webhook-Trigger-Knoten mit diesem Pfad haben)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "webhook_path": {"type": "string"},
                "data": {"type": "object", "description": "Nutzdaten, die an den Webhook gesendet werden"},
            },
            "required": ["webhook_path"],
        },
        handler=_trigger_n8n_workflow,
    )
)

register(
    Tool(
        name="call_api",
        description=(
            "Ruft eine oeffentliche HTTP-API auf (GET/POST/PUT/PATCH/DELETE). Interne/private "
            "Netzwerkziele werden abgelehnt."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
                "body": {"description": "JSON-Body (Objekt/Array) oder String"},
                "headers": {"type": "object"},
            },
            "required": ["url"],
        },
        handler=_call_api,
    )
)
