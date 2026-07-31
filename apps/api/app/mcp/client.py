"""MCP client: connects to a user-configured MCP server (stdio subprocess or SSE
endpoint), lists its tools, or calls one.

Connects fresh for every call rather than keeping a persistent session - simpler and
correct across the API's request-scoped async model (the same trade-off already made
for browser/terminal sessions elsewhere in this codebase), at the cost of a re-handshake
per call. Fine for personal-use call volumes; would need a session pool before this
scales to frequent, latency-sensitive use.
"""
import json
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.core import crypto
from app.models.mcp_server import McpServer
from app.orchestrator.tools.ssrf_guard import is_safe_url

_TIMEOUT_SECONDS = 20.0


async def _open_session(server: McpServer, stack: AsyncExitStack) -> ClientSession:
    if server.transport == "stdio":
        if not server.command:
            raise ValueError("Server hat kein 'command' konfiguriert.")
        env = {key: crypto.decrypt(value) for key, value in (server.env or {}).items()}
        params = StdioServerParameters(command=server.command, args=list(server.args or []), env=(env or None))
        read_stream, write_stream = await stack.enter_async_context(stdio_client(params))
    elif server.transport == "sse":
        if not server.url:
            raise ValueError("Server hat keine 'url' konfiguriert.")
        # F6 (docs/FIX_PLAN.md, S6 in docs/AUDIT_REPORT.md): sse_client() connects
        # directly with no SSRF guard of its own - unlike read_page/call_api (F4/F7),
        # it isn't built on httpx, so there's no pinned_request() equivalent to hook
        # into here. is_safe_url() is a resolve-then-decide pre-check (same residual
        # DNS-rebinding TOCTOU caveat as F5's browser guard), which is what the fix
        # plan calls for at this call site.
        if not is_safe_url(server.url):
            raise ValueError("MCP-Server-URL abgelehnt: nur oeffentliche http(s)-Adressen sind erlaubt.")
        read_stream, write_stream = await stack.enter_async_context(sse_client(server.url))
    else:
        raise ValueError(f"Unbekannter Transport: {server.transport}")

    session = await stack.enter_async_context(
        ClientSession(read_stream, write_stream, read_timeout_seconds=_TIMEOUT_SECONDS)
    )
    await session.initialize()
    return session


async def list_tools(server: McpServer) -> list[dict]:
    async with AsyncExitStack() as stack:
        session = await _open_session(server, stack)
        result = await session.list_tools()
        return [{"name": t.name, "description": t.description} for t in result.tools]


async def call_tool(server: McpServer, tool_name: str, arguments: dict) -> str:
    async with AsyncExitStack() as stack:
        session = await _open_session(server, stack)
        result = await session.call_tool(tool_name, arguments)

    parts = []
    for block in result.content:
        text = getattr(block, "text", None)
        parts.append(text if text is not None else json.dumps(block.model_dump(), ensure_ascii=False))
    output = "\n".join(parts) if parts else "(keine Ausgabe)"
    return f"MCP-Tool-Fehler: {output}" if result.is_error else output
