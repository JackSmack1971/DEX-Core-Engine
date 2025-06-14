"""Routine database maintenance tasks."""

from __future__ import annotations

import os
from typing import Iterable

import asyncpg

from logger import get_logger
from utils.retry import retry_async
from exceptions import ConfigurationError, DatabaseMaintenanceError

logger = get_logger("db_maint")


def _pg_dsn() -> str:
    url = os.getenv("DATABASE__URL")
    if not url:
        raise ConfigurationError("DATABASE__URL missing")
    return url.replace("+asyncpg", "")


async def _exec(query: str) -> None:
    conn_str = _pg_dsn()
    async with asyncpg.connect(conn_str) as conn:
        await conn.execute(query)


async def vacuum_analyze() -> None:
    """Run VACUUM ANALYZE."""
    async def _run() -> None:
        await _exec("VACUUM (ANALYZE)")

    await retry_async(_run)


async def check_indexes() -> list[str]:
    """Return names of indexes not ready."""
    async def _run() -> Iterable[str]:
        conn_str = _pg_dsn()
        async with asyncpg.connect(conn_str) as conn:
            rows = await conn.fetch(
                "SELECT indexrelid::regclass::text AS name FROM pg_index "
                "WHERE NOT indisready"
            )
            return [r["name"] for r in rows]

    try:
        result = await retry_async(_run)
        return list(result)
    except Exception as exc:  # noqa: BLE001
        logger.error("Index check failed: %s", exc)
        raise DatabaseMaintenanceError("index check failed") from exc
