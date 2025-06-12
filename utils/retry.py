"""Exponential backoff retry helpers."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import Any

from logger import get_logger

logger = get_logger("retry")


async def retry_async(
    func: Callable[..., Awaitable[Any]],
    *args: Any,
    retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 30.0,
    **kwargs: Any,
) -> Any:
    """Retry ``func`` using exponential backoff with jitter."""
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - pass through
            if attempt == retries - 1:
                raise
            delay = min(base_delay * 2**attempt, max_delay)
            delay += random.uniform(0, delay / 2)
            logger.warning("Retrying after error: %s", exc)
            await asyncio.sleep(delay)
    raise RuntimeError("unreachable")  # pragma: no cover
