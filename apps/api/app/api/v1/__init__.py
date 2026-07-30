from fastapi import APIRouter

from app.api.v1 import (
    agents,
    auth,
    browser,
    conversations,
    files,
    health,
    knowledge,
    notes,
    projects,
    tasks,
    terminal,
    vision,
    voice,
)

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(agents.router)
router.include_router(conversations.router)
router.include_router(knowledge.router)
router.include_router(projects.router)
router.include_router(tasks.router)
router.include_router(browser.router)
router.include_router(terminal.router)
router.include_router(vision.router)
router.include_router(voice.router)
router.include_router(files.router)
router.include_router(notes.router)
