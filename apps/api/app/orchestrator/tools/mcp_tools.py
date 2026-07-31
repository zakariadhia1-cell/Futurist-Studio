"""Lets agents discover and call tools on the user's configured MCP servers - see
app/models/mcp_server.py for why this is FUTURIST OS's plugin mechanism rather than a
separate plugin-loader system."""
from sqlalchemy import select

from app.core import audit
from app.mcp import client as mcp_client
from app.models.mcp_server import McpServer
from app.orchestrator.tool_registry import Tool, ToolContext, register


async def _get_enabled_server(name: str, ctx: ToolContext) -> McpServer | None:
    result = await ctx.db.execute(
        select(McpServer).where(
            McpServer.user_id == ctx.user_id, McpServer.name == name, McpServer.enabled.is_(True)
        )
    )
    return result.scalar_one_or_none()


async def _list_mcp_servers(arguments: dict, ctx: ToolContext) -> str:
    result = await ctx.db.execute(
        select(McpServer).where(McpServer.user_id == ctx.user_id, McpServer.enabled.is_(True))
    )
    servers = result.scalars().all()
    if not servers:
        return "Keine MCP-Server konfiguriert (siehe Einstellungen > MCP-Server)."
    return "Konfigurierte MCP-Server:\n" + "\n".join(f"- {s.name} ({s.transport})" for s in servers)


async def _list_mcp_tools(arguments: dict, ctx: ToolContext) -> str:
    name = str(arguments.get("server_name", "")).strip()
    server = await _get_enabled_server(name, ctx)
    if server is None:
        return f"Kein aktivierter MCP-Server mit dem Namen '{name}' gefunden."
    try:
        tools = await mcp_client.list_tools(server)
    except Exception as exc:
        return f"Verbindung zu MCP-Server '{name}' fehlgeschlagen: {exc}"
    if not tools:
        return f"MCP-Server '{name}' bietet keine Tools an."
    return f"Tools auf '{name}':\n" + "\n".join(
        f"- {t['name']}: {t.get('description') or '(keine Beschreibung)'}" for t in tools
    )


async def _call_mcp_tool(arguments: dict, ctx: ToolContext) -> str:
    server_name = str(arguments.get("server_name", "")).strip()
    tool_name = str(arguments.get("tool_name", "")).strip()
    tool_arguments = arguments.get("arguments") or {}
    if not isinstance(tool_arguments, dict):
        return "arguments muss ein Objekt sein."

    server = await _get_enabled_server(server_name, ctx)
    if server is None:
        return f"Kein aktivierter MCP-Server mit dem Namen '{server_name}' gefunden."
    try:
        result = await mcp_client.call_tool(server, tool_name, tool_arguments)
    except Exception as exc:
        return f"MCP-Tool-Aufruf fehlgeschlagen: {exc}"

    audit.record(
        ctx.db,
        user_id=ctx.user_id,
        action="automation_agent.call_mcp_tool",
        resource_type="mcp_tool",
        resource_id=f"{server_name}/{tool_name}",
    )
    await ctx.db.commit()
    return result


register(
    Tool(
        name="list_mcp_servers",
        description="Listet die aktivierten MCP-Server des Nutzers auf.",
        input_schema={"type": "object", "properties": {}},
        handler=_list_mcp_servers,
    )
)

register(
    Tool(
        name="list_mcp_tools",
        description="Listet die verfuegbaren Tools eines konfigurierten MCP-Servers auf.",
        input_schema={
            "type": "object",
            "properties": {"server_name": {"type": "string"}},
            "required": ["server_name"],
        },
        handler=_list_mcp_tools,
    )
)

register(
    Tool(
        name="call_mcp_tool",
        description="Ruft ein Tool auf einem konfigurierten MCP-Server auf.",
        input_schema={
            "type": "object",
            "properties": {
                "server_name": {"type": "string"},
                "tool_name": {"type": "string"},
                "arguments": {"type": "object", "description": "Argumente fuer das MCP-Tool"},
            },
            "required": ["server_name", "tool_name"],
        },
        handler=_call_mcp_tool,
    )
)
