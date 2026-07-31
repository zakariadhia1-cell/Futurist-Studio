"""FUTURIST OS API - FastAPI entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.orchestrator.tools  # noqa: F401 - import side effect: registers built-in tools
from app.api.v1 import router as v1_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.live import browser_manager
from app.ws.browser import router as browser_ws_router
from app.ws.chat import router as chat_ws_router
from app.ws.terminal import router as terminal_ws_router

settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    # Playwright's async driver is bound to the event loop it was started in, so it must
    # be closed here rather than left to garbage collection.
    await browser_manager.shutdown()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")
app.include_router(chat_ws_router)
app.include_router(browser_ws_router)
app.include_router(terminal_ws_router)
