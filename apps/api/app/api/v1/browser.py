from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.live import browser_manager
from app.models.user import User
from app.schemas.browser import BrowserSessionList, BrowserSessionRead

router = APIRouter(prefix="/browser", tags=["browser"])


@router.get("/sessions", response_model=BrowserSessionList)
async def list_sessions(user: User = Depends(get_current_user)) -> BrowserSessionList:
    return BrowserSessionList(sessions=browser_manager.list_sessions(user.id))


@router.post("/sessions", response_model=BrowserSessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(user: User = Depends(get_current_user)) -> BrowserSessionRead:
    session = await browser_manager.create_session(user.id)
    return BrowserSessionRead(id=session.id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_session(session_id: str, user: User = Depends(get_current_user)) -> None:
    closed = await browser_manager.close_session(session_id, user.id)
    if not closed:
        raise HTTPException(status_code=404, detail="Browser-Session nicht gefunden.")
