"""Asynchronous circuit breaker for external service calls."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from logger import logger
from exceptions import ServiceUnavailableError


class CircuitBreaker:
    """Simple async circuit breaker implementation."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._state = "closed"
        self._opened_at = 0.0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
        """Execute ``func`` with circuit breaker logic."""
        async with self._lock:
            if self._state == "open":
                if time.time() - self._opened_at < self.recovery_timeout:
                    raise ServiceUnavailableError("circuit open")
                self._state = "half-open"
            try:
                result = await func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - re-raise after state update
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._state = "open"
                    self._opened_at = time.time()
                    logger.error("Circuit opened after failures: %s", self._failure_count)
                raise
            else:
                if self._state in {"half-open", "open"}:
                    logger.info("Circuit closed")
                self._state = "closed"
                self._failure_count = 0
                return result
