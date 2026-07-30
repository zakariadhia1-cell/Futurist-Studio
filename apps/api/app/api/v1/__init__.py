from fastapi import APIRouter

from app.api.v1 import agents, auth, conversations, health, knowledge

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(agents.router)
router.include_router(conversations.router)
router.include_router(knowledge.router)
