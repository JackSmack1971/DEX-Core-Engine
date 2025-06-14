from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from redis.asyncio import Redis

from logger import get_logger
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async


class RedisCacheError(Exception):
    """Raised when Redis cache operations fail."""


class RedisCache:
    """Async Redis cache for market data and strategy performance."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        password: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db or int(os.getenv("REDIS_DB", "0"))
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.timeout = timeout or float(os.getenv("REDIS_TIMEOUT", "5"))
        self.logger = get_logger("redis_cache")
        self._client = Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
        )
        self._circuit = CircuitBreaker()

    async def _set(self, key: str, value: str, expire: int) -> None:
        await self._client.set(key, value, ex=expire)

    async def _get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set_market_data(self, pair: str, data: Any, expire: int = 300) -> None:
        if not pair:
            raise RedisCacheError("invalid pair")
        value = json.dumps(data)

        async def _op() -> None:
            await self._set(f"market:{pair}", value, expire)

        try:
            await asyncio.wait_for(
                self._circuit.call(retry_async, _op), self.timeout
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Set market data failed: %s", exc)
            raise RedisCacheError(str(exc)) from exc

    async def get_market_data(self, pair: str) -> Any | None:
        if not pair:
            raise RedisCacheError("invalid pair")

        async def _op() -> Any | None:
            return await self._get(f"market:{pair}")

        try:
            data = await asyncio.wait_for(
                self._circuit.call(retry_async, _op), self.timeout
            )
            return json.loads(data) if data is not None else None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Get market data failed: %s", exc)
            raise RedisCacheError(str(exc)) from exc

    async def set_strategy_performance(
        self, strategy: str, value: float, expire: int = 3600
    ) -> None:
        if not strategy:
            raise RedisCacheError("invalid strategy")

        async def _op() -> None:
            await self._set(f"perf:{strategy}", str(value), expire)

        try:
            await asyncio.wait_for(
                self._circuit.call(retry_async, _op), self.timeout
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Set strategy performance failed: %s", exc)
            raise RedisCacheError(str(exc)) from exc

    async def get_strategy_performance(self, strategy: str) -> float | None:
        if not strategy:
            raise RedisCacheError("invalid strategy")

        async def _op() -> str | None:
            return await self._get(f"perf:{strategy}")

        try:
            data = await asyncio.wait_for(
                self._circuit.call(retry_async, _op), self.timeout
            )
            return float(data) if data is not None else None
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Get strategy performance failed: %s", exc)
            raise RedisCacheError(str(exc)) from exc

__all__ = ["RedisCache", "RedisCacheError"]
