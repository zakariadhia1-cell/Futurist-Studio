from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.live import terminal_manager
from app.models.user import User
from app.schemas.terminal import TerminalSessionList, TerminalSessionRead

router = APIRouter(prefix="/terminal", tags=["terminal"])


@router.get("/sessions", response_model=TerminalSessionList)
async def list_sessions(user: User = Depends(get_current_user)) -> TerminalSessionList:
    return TerminalSessionList(sessions=terminal_manager.list_sessions(user.id))


@router.post("/sessions", response_model=TerminalSessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(user: User = Depends(get_current_user)) -> TerminalSessionRead:
    session = await terminal_manager.create_session(user.id)
    return TerminalSessionRead(id=session.id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_session(session_id: str, user: User = Depends(get_current_user)) -> None:
    closed = await terminal_manager.close_session(session_id, user.id)
    if not closed:
        raise HTTPException(status_code=404, detail="Terminal-Session nicht gefunden.")
