"""WebSocket chat channel: /ws/chat/{conversation_id}.

Browsers can't set custom headers on a WebSocket handshake, so the access token travels
as a query parameter (?token=...) instead of an Authorization header.

Envelope format (both directions): {"type": "...", "payload": {...}}
Client -> server: {"type": "user_message", "content": "..."}
Server -> client: {"type": "token", "payload": {"text": "..."}}
             then: {"type": "done", "payload": {}}
          or (per-message, connection stays open): {"type": "error", "payload": {"message": "..."}}
"""
import json
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.base import get_db
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.model_config import ModelConfig
from app.orchestrator.runner import stream_agent_reply

router = APIRouter()


@router.websocket("/ws/chat/{conversation_id}")
async def chat_socket(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    # db comes through the same overridable get_db dependency as the REST endpoints
    # (important for tests, which point it at a separate test database/session factory).
    token = websocket.query_params.get("token")
    payload = decode_token(token) if token else None
    if payload is None or payload.get("type") != "access":
        await websocket.close(code=4401)
        return
    user_id = uuid.UUID(payload["sub"])

    await websocket.accept()

    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    if conversation is None or conversation.user_id != user_id:
        await websocket.send_json({"type": "error", "payload": {"message": "Konversation nicht gefunden."}})
        await websocket.close(code=4404)
        return

    agent = (await db.execute(select(Agent).where(Agent.id == conversation.agent_id))).scalar_one()
    model_config = (
        await db.execute(select(ModelConfig).where(ModelConfig.id == agent.default_model_id))
    ).scalar_one()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            if data.get("type") != "user_message":
                continue
            content = str(data.get("content", "")).strip()
            if not content:
                continue

            db.add(Message(conversation_id=conversation.id, role="user", content=content))
            await db.commit()

            try:
                history = (
                    await db.execute(
                        select(Message)
                        .where(Message.conversation_id == conversation.id)
                        .order_by(Message.created_at)
                    )
                ).scalars().all()

                full_reply = ""
                async for chunk in stream_agent_reply(
                    agent, model_config.provider, model_config.model_name, history
                ):
                    full_reply += chunk
                    await websocket.send_json({"type": "token", "payload": {"text": chunk}})

                db.add(
                    Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=full_reply,
                        model_used=model_config.model_name,
                    )
                )
                await db.commit()
                await websocket.send_json({"type": "done", "payload": {}})
            except Exception as exc:  # noqa: BLE001 - surfaced to the client, connection stays open
                await websocket.send_json({"type": "error", "payload": {"message": str(exc)}})
    except WebSocketDisconnect:
        pass
