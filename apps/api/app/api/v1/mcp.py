import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
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
    payload: McpServerCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> McpServerRead:
    server = McpServer(user_id=user.id, **payload.model_dump())
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
    server_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[McpToolInfo]:
    server = await _get_owned_server(server_id, db, user)
    try:
        tools = await mcp_client.list_tools(server)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Verbindung zum MCP-Server fehlgeschlagen: {exc}") from None
    return [McpToolInfo(**t) for t in tools]
