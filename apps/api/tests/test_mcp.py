import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

import app.orchestrator.tools  # noqa: F401 - registers built-in tools
from app.orchestrator.tool_registry import ToolContext, execute_tool
from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio

_ECHO_SERVER_SCRIPT = str(Path(__file__).parent / "fixtures" / "echo_mcp_server.py")


async def _get_user_id(client) -> uuid.UUID:
    token = await register_and_login(client)
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return uuid.UUID(me.json()["id"])


async def _auth_headers(client) -> dict:
    token = await register_and_login(client)
    return {"Authorization": f"Bearer {token}"}


async def test_mcp_servers_require_auth(client):
    assert (await client.get("/api/v1/mcp/servers")).status_code == 401


async def test_non_admin_member_cannot_create_or_invoke_mcp_servers(client):
    """F1 (docs/FIX_PLAN.md, S1 in docs/AUDIT_REPORT.md): a self-registered member must
    not be able to register a stdio MCP server (arbitrary command execution on the API
    host) or invoke tools on one - only the admin can."""
    await _auth_headers(client)  # first user in this fresh DB, becomes admin - not used further
    member_token = await register_and_login(client, email="member@futurist.os")
    member_headers = {"Authorization": f"Bearer {member_token}"}

    create = await client.post(
        "/api/v1/mcp/servers",
        json={"name": "evil", "transport": "stdio", "command": "/bin/bash", "args": ["-c", "id"]},
        headers=member_headers,
    )
    assert create.status_code == 403

    # Even a server the member somehow owned couldn't be listed/invoked as a member -
    # verified against a random id since the create above was correctly rejected.
    fake_id = str(uuid.uuid4())
    assert (await client.get(f"/api/v1/mcp/servers/{fake_id}/tools", headers=member_headers)).status_code == 403


async def test_create_server_validates_transport_fields(client):
    headers = await _auth_headers(client)
    missing_command = await client.post(
        "/api/v1/mcp/servers", json={"name": "x", "transport": "stdio"}, headers=headers
    )
    assert missing_command.status_code == 422

    missing_url = await client.post("/api/v1/mcp/servers", json={"name": "x", "transport": "sse"}, headers=headers)
    assert missing_url.status_code == 422


async def test_server_crud_roundtrip(client):
    headers = await _auth_headers(client)

    create = await client.post(
        "/api/v1/mcp/servers",
        json={"name": "echo", "transport": "stdio", "command": sys.executable, "args": [_ECHO_SERVER_SCRIPT]},
        headers=headers,
    )
    assert create.status_code == 201
    server_id = create.json()["id"]

    listing = await client.get("/api/v1/mcp/servers", headers=headers)
    assert [s["id"] for s in listing.json()] == [server_id]

    update = await client.patch(f"/api/v1/mcp/servers/{server_id}", json={"enabled": False}, headers=headers)
    assert update.status_code == 200
    assert update.json()["enabled"] is False

    delete = await client.delete(f"/api/v1/mcp/servers/{server_id}", headers=headers)
    assert delete.status_code == 204
    assert (await client.get("/api/v1/mcp/servers", headers=headers)).json() == []


async def test_list_server_tools_uses_real_stdio_server(client):
    headers = await _auth_headers(client)
    create = await client.post(
        "/api/v1/mcp/servers",
        json={"name": "echo", "transport": "stdio", "command": sys.executable, "args": [_ECHO_SERVER_SCRIPT]},
        headers=headers,
    )
    server_id = create.json()["id"]

    resp = await client.get(f"/api/v1/mcp/servers/{server_id}/tools", headers=headers)
    assert resp.status_code == 200
    tools = resp.json()
    assert tools == [{"name": "echo", "description": "Gibt den uebergebenen Text zurueck."}]


async def test_servers_are_isolated_per_user(client):
    # The first registered user in this test's fresh DB is always admin (see auth.py) -
    # required now that create_server/list_server_tools are admin-gated (F1).
    headers_a = await _auth_headers(client)
    create = await client.post(
        "/api/v1/mcp/servers",
        json={"name": "privat", "transport": "sse", "url": "http://example.invalid/mcp"},
        headers=headers_a,
    )
    server_id = create.json()["id"]

    token_b = await register_and_login(client, email="b-mcp@futurist.os")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    assert (await client.get("/api/v1/mcp/servers", headers=headers_b)).json() == []
    # user B is a regular member, not admin - blocked before the ownership check even
    # runs (403), not the 404 a non-owning admin would see.
    assert (await client.get(f"/api/v1/mcp/servers/{server_id}/tools", headers=headers_b)).status_code == 403
    assert (await client.delete(f"/api/v1/mcp/servers/{server_id}", headers=headers_b)).status_code == 404


async def test_server_env_is_encrypted_at_rest(client, db_session, monkeypatch):
    from cryptography.fernet import Fernet

    from app.core import crypto
    from app.core.config import get_settings
    from app.models.mcp_server import McpServer

    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    get_settings.cache_clear()
    crypto._get_fernet.cache_clear()
    try:
        headers = await _auth_headers(client)
        create = await client.post(
            "/api/v1/mcp/servers",
            json={
                "name": "with-secret",
                "transport": "stdio",
                "command": "echo",
                "env": {"API_KEY": "super-secret-value"},
            },
            headers=headers,
        )
        server_id = create.json()["id"]

        result = await db_session.execute(select(McpServer).where(McpServer.id == uuid.UUID(server_id)))
        server = result.scalar_one()
        assert server.env["API_KEY"] != "super-secret-value"
        assert crypto.decrypt(server.env["API_KEY"]) == "super-secret-value"
    finally:
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        get_settings.cache_clear()
        crypto._get_fernet.cache_clear()


async def test_list_mcp_servers_tool_reports_none_configured(client, db_session):
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)
    result = await execute_tool("list_mcp_servers", {}, ctx)
    assert "Keine MCP-Server" in result


async def test_mcp_tools_end_to_end_via_real_server(client, db_session):
    user_id = await _get_user_id(client)
    ctx = ToolContext(db=db_session, user_id=user_id)

    from app.models.mcp_server import McpServer

    db_session.add(
        McpServer(
            user_id=user_id,
            name="echo",
            transport="stdio",
            command=sys.executable,
            args=[_ECHO_SERVER_SCRIPT],
            env={},
            enabled=True,
        )
    )
    await db_session.commit()

    servers_result = await execute_tool("list_mcp_servers", {}, ctx)
    assert "echo" in servers_result

    tools_result = await execute_tool("list_mcp_tools", {"server_name": "echo"}, ctx)
    assert "echo:" in tools_result

    call_result = await execute_tool(
        "call_mcp_tool", {"server_name": "echo", "tool_name": "echo", "arguments": {"text": "Hallo Z"}}, ctx
    )
    assert call_result == "Echo: Hallo Z"

    unknown_result = await execute_tool("call_mcp_tool", {"server_name": "nicht-vorhanden", "tool_name": "x"}, ctx)
    assert "Kein aktivierter MCP-Server" in unknown_result
