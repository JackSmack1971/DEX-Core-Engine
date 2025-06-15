from __future__ import annotations

"""Asynchronous rate limiting utilities using Redis."""

import asyncio
import os
from functools import wraps
from typing import Any, Awaitable, Callable

from fastapi import HTTPException, status
from redis.asyncio import Redis

from exceptions import RateLimitError
from logger import get_logger
from utils.retry import retry_async

_logger = get_logger("rate_limiting")
_client: Redis | None = None


def get_redis() -> Redis:
    """Return a cached Redis client instance."""
    global _client
    if _client is None:
        _client = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True,
        )
    return _client


async def check_rate_limit(user_id: str, scope: str, limit: int, window: int) -> None:
    """Increment request counter and enforce ``limit`` within ``window`` seconds."""
    if not user_id or not scope or limit <= 0 or window <= 0:
        raise RateLimitError("invalid parameters")
    key = f"rl:{user_id}:{scope}"
    timeout = float(os.getenv("REDIS_TIMEOUT", "5"))
    client = get_redis()

    async def _op() -> int:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window)
        return int(count)

    try:
        count = await asyncio.wait_for(retry_async(_op), timeout)
    except Exception as exc:  # noqa: BLE001
        _logger.error("Rate limit check failed: %s", exc)
        raise RateLimitError("rate limit check failed") from exc
    if count > limit:
        raise RateLimitError("request limit exceeded")


def rate_limit(scope: str, limit: int, window: int) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Decorate FastAPI endpoints to enforce rate limits."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = kwargs.get("current_user")
            username = getattr(user, "username", None)
            if username is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid user")
            try:
                await check_rate_limit(username, scope, limit, window)
            except RateLimitError as exc:
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, exc.message) from exc
            return await func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["rate_limit", "check_rate_limit", "get_redis"]
