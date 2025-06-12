from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from logger import get_logger
from observability.metrics import API_LATENCY


def log_and_measure(component: str, warn_ms: int) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Decorator to log duration of async calls."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(component)
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            except Exception:
                logger.exception("%s failed", func.__name__)
                raise
            finally:
                duration = (time.perf_counter() - start) * 1000
                API_LATENCY.observe(duration / 1000)
                level = 'warning' if duration > warn_ms else 'debug'
                getattr(logger, level)(
                    "%s completed", func.__name__, extra={"duration_ms": duration}
                )
        return wrapper

    return decorator

__all__ = ["log_and_measure"]
