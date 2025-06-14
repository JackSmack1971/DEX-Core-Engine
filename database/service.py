from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DatabaseSettings
from exceptions import ServiceUnavailableError
from logger import get_logger
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async


class DatabaseService:
    """Async database service with connection pooling."""

    def __init__(self, config: DatabaseSettings) -> None:
        self._config = config
        self.logger = get_logger("database_service")
        engine_kwargs = {"echo": config.echo}
        if str(config.url).startswith("postgresql"):
            engine_kwargs.update(
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_timeout=config.pool_timeout,
                pool_recycle=config.pool_recycle,
            )
        self._engine = create_async_engine(config.url, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            self._engine, expire_on_commit=False
        )
        self._circuit = CircuitBreaker()

    async def get_session(self) -> AsyncSession:
        async def _acquire() -> AsyncSession:
            return self._sessionmaker()

        try:
            return await self._circuit.call(retry_async, _acquire)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Session acquisition failed: %s", exc)
            raise ServiceUnavailableError("db session failure") from exc

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        session = await self.get_session()
        try:
            async with session.begin():
                yield session
        except Exception:  # noqa: BLE001
            await session.rollback()
            raise
        finally:
            await session.close()

