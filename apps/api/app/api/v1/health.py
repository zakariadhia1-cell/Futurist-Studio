from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.base import get_db

router = APIRouter(tags=["system"])
settings = get_settings()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    db_ok = True
    try:
        await db.execute(text("select 1"))
    except Exception:
        db_ok = False

    redis_ok = True
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.aclose()
    except Exception:
        redis_ok = False

    return {"status": "ok" if db_ok and redis_ok else "degraded", "database": db_ok, "redis": redis_ok}
