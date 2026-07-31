"""WebSocket channel: /ws/terminal/{session_id}.

Client -> server: {"type": "input", "data": "ls -la\\n"}
              or: {"type": "resize", "rows": 24, "cols": 80}
Server -> client: {"type": "output", "data": "..."}
              or: {"type": "closed"}  (the shell process exited)
"""
import asyncio
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.live import terminal_manager

router = APIRouter()


@router.websocket("/ws/terminal/{session_id}")
async def terminal_socket(websocket: WebSocket, session_id: str) -> None:
    token = websocket.query_params.get("token")
    payload = decode_token(token) if token else None
    if payload is None or payload.get("type") != "access":
        await websocket.close(code=4401)
        return
    user_id = uuid.UUID(payload["sub"])

    session = terminal_manager.get_session(session_id, user_id)
    if session is None:
        await websocket.close(code=4404)
        return

    await websocket.accept()

    async def pump_output() -> None:
        while True:
            chunk = await session.output_queue.get()
            if chunk is None:
                await websocket.send_json({"type": "closed"})
                return
            await websocket.send_json({"type": "output", "data": chunk.decode("utf-8", errors="replace")})

    pump_task = asyncio.create_task(pump_output())

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            if data.get("type") == "input":
                terminal_manager.write_input(session, str(data.get("data", "")))
            elif data.get("type") == "resize":
                terminal_manager.resize(session, int(data.get("rows", 24)), int(data.get("cols", 80)))
    except WebSocketDisconnect:
        pass
    finally:
        pump_task.cancel()
