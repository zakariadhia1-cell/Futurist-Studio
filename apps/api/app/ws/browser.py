"""WebSocket channel: /ws/browser/{session_id}.

Client -> server: {"type": "action", "action": "navigate"|"click"|"fill"|"go_back"|"screenshot", "args": {...}}
Server -> client: {"type": "screenshot", "payload": {"image_base64": "..."}}
              and: {"type": "result", "payload": {"message": "..."}}
           or (per-action, connection stays open): {"type": "error", "payload": {"message": "..."}}
"""
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.live import browser_manager

router = APIRouter()


@router.websocket("/ws/browser/{session_id}")
async def browser_socket(websocket: WebSocket, session_id: str) -> None:
    token = websocket.query_params.get("token")
    payload = decode_token(token) if token else None
    if payload is None or payload.get("type") != "access":
        await websocket.close(code=4401)
        return
    user_id = uuid.UUID(payload["sub"])

    session = browser_manager.get_session(session_id, user_id)
    if session is None:
        await websocket.close(code=4404)
        return

    await websocket.accept()

    async def send_screenshot() -> None:
        image_base64 = await browser_manager.screenshot_base64(session)
        await websocket.send_json({"type": "screenshot", "payload": {"image_base64": image_base64}})

    await send_screenshot()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            if data.get("type") != "action":
                continue
            action = data.get("action", "")
            args = data.get("args", {})

            try:
                message = await browser_manager.execute_action(session, action, args)
                await websocket.send_json({"type": "result", "payload": {"message": message}})
                await send_screenshot()
            except Exception as exc:  # noqa: BLE001 - surfaced to the client, connection stays open
                await websocket.send_json({"type": "error", "payload": {"message": str(exc)}})
    except WebSocketDisconnect:
        pass
