"""Async database backup utilities."""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from urllib.parse import urlparse

from logger import get_logger
from utils.retry import retry_async
from exceptions import ConfigurationError, DatabaseBackupError

logger = get_logger("db_backup")


def _parse_pg_url(url: str) -> str:
    parsed = urlparse(url.replace("+asyncpg", ""))
    if not parsed.scheme or not parsed.path or not parsed.hostname:
        raise ConfigurationError("Invalid DATABASE__URL")
    pwd = f":{parsed.password}" if parsed.password else ""
    port = f":{parsed.port}" if parsed.port else ""
    db = parsed.path.lstrip("/")
    user = parsed.username or ""
    return f"postgresql://{user}{pwd}@{parsed.hostname}{port}/{db}"


async def _exec_pg_dump(dsn: str, path: Path, timeout: int) -> None:
    env = os.environ.copy()
    env.setdefault("PGPASSWORD", urlparse(dsn).password or "")
    process = await asyncio.create_subprocess_exec(
        "pg_dump", "--dbname", dsn, "--file", str(path), env=env
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
    if process.returncode != 0:
        logger.error("pg_dump failed: %s", stderr.decode())
        raise DatabaseBackupError("pg_dump failed")
    if stdout:
        logger.info("pg_dump: %s", stdout.decode().strip())


async def encrypt_backup(path: Path) -> Path:
    """Encrypt the backup file (stub)."""
    if not path.exists():
        raise DatabaseBackupError("backup file missing")
    dest = path.with_suffix(path.suffix + ".enc")
    await asyncio.to_thread(shutil.copyfile, path, dest)
    return dest


async def run_backup(output_path: str, timeout: int = 60) -> Path:
    """Run pg_dump and encrypt the output."""
    if not output_path:
        raise ValueError("output_path required")
    url = os.getenv("DATABASE__URL")
    if not url:
        raise ConfigurationError("DATABASE__URL missing")
    dsn = _parse_pg_url(url)
    path = Path(output_path)

    async def _dump() -> None:
        await _exec_pg_dump(dsn, path, timeout)

    await retry_async(_dump)
    return await encrypt_backup(path)
