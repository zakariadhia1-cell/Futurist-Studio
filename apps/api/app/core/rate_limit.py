"""A small Redis-backed fixed-window rate limiter, applied explicitly to the handful of
endpoints where it matters (auth) rather than as blanket middleware - each call site picks
its own limit/window. Fixed-window (not sliding/token-bucket): simpler, and "at most 2x the
limit at a window boundary" is an acceptable trade-off for brute-force protection on a
personal system, not a hard SLA."""
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis

from app.core.config import get_settings


def rate_limiter(key_prefix: str, *, limit: int, window_seconds: int) -> Callable[[Request], Awaitable[None]]:
    async def _dependency(request: Request) -> None:
        settings = get_settings()
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{key_prefix}:{client_ip}"

        redis = Redis.from_url(settings.REDIS_URL)
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window_seconds)
        finally:
            await redis.aclose()

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Zu viele Versuche. Bitte in {window_seconds} Sekunden erneut versuchen.",
            )

    return _dependency
