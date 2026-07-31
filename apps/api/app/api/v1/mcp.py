import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.core.dependencies import get_current_user, require_admin
from app.db.base import get_db
from app.mcp import client as mcp_client
from app.models.mcp_server import McpServer
from app.models.user import User
from app.schemas.mcp import McpServerCreate, McpServerRead, McpServerUpdate, McpToolInfo

router = APIRouter(prefix="/mcp", tags=["mcp"])


async def _get_owned_server(server_id: uuid.UUID, db: AsyncSession, user: User) -> McpServer:
    result = await db.execute(select(McpServer).where(McpServer.id == server_id))
    server = result.scalar_one_or_none()
    if server is None or server.user_id != user.id:
        raise HTTPException(status_code=404, detail="MCP-Server nicht gefunden.")
    return server


@router.get("/servers", response_model=list[McpServerRead])
async def list_servers(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[McpServerRead]:
    result = await db.execute(
        select(McpServer).where(McpServer.user_id == user.id).order_by(McpServer.created_at.desc())
    )
    return [McpServerRead.model_validate(s) for s in result.scalars().all()]


@router.post("/servers", response_model=McpServerRead, status_code=status.HTTP_201_CREATED)
async def create_server(
    payload: McpServerCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)
) -> McpServerRead:
    # F1 (docs/FIX_PLAN.md, S1 in docs/AUDIT_REPORT.md): stdio transport lets the
    # caller pick an arbitrary command/args, executed as a subprocess on the API host
    # the moment anyone lists or calls its tools (see list_server_tools below) - admin
    # only, same trust level as the Terminal feature.
    data = payload.model_dump()
    data["env"] = {key: crypto.encrypt(value) for key, value in data["env"].items()}
    server = McpServer(user_id=user.id, **data)
    db.add(server)
    await db.commit()
    await db.refresh(server)
    return McpServerRead.model_validate(server)


@router.patch("/servers/{server_id}", response_model=McpServerRead)
async def update_server(
    server_id: uuid.UUID,
    payload: McpServerUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> McpServerRead:
    server = await _get_owned_server(server_id, db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(server, field, value)
    await db.commit()
    await db.refresh(server)
    return McpServerRead.model_validate(server)


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    server = await _get_owned_server(server_id, db, user)
    await db.delete(server)
    await db.commit()


@router.get("/servers/{server_id}/tools", response_model=list[McpToolInfo])
async def list_server_tools(
    server_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)
) -> list[McpToolInfo]:
    # F1: this is the endpoint that actually connects (subprocess-execs for stdio
    # transport) - admin-gated for the same reason as create_server above. Ownership
    # scoping in _get_owned_server would already stop a member from reaching another
    # user's server, but since only admins can create one at all after the fix above,
    # this is defense-in-depth against that invariant ever being weakened later.
    server = await _get_owned_server(server_id, db, user)
    try:
        tools = await mcp_client.list_tools(server)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Verbindung zum MCP-Server fehlgeschlagen: {exc}") from None
    return [McpToolInfo(**t) for t in tools]
