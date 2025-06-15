from types import SimpleNamespace
from typing import Any
import hashlib
from sqlalchemy import select

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from audit import AsyncAuditLogger
from config import DatabaseSettings
from database.services import DatabaseService
from database.models import Base, AuditLog
from cryptography.fernet import Fernet


@pytest.mark.asyncio
async def test_insert_and_fetch(monkeypatch) -> None:
    def fake_engine(url: str, **_: Any):
        return create_async_engine("sqlite+aiosqlite:///:memory:")

    monkeypatch.setattr(
        "database.services.database.create_async_engine",
        fake_engine,
    )
    settings = DatabaseSettings(
        url="postgresql+asyncpg://user:pass@localhost/test",
        encryption_key="8ZUJoRb_GXBDTPjL_Q0msBmE0vpo-hDabEIUkfGfs04=",
        audit_encryption_key="oh-tvfXPINv_kIWFlUufdfrwqcoYlEtp6SuMziSRVLI=",
        query_timeout=30,
    )
    service = DatabaseService(settings)
    async with service._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger = AsyncAuditLogger(service, settings.audit_encryption_key)
    logger._circuit = SimpleNamespace(call=lambda f, *a, **k: f(*a, **k))

    cid = await logger.insert_logs([("login", "user admin")])
    logs = await logger.get_logs(cid)
    assert len(logs) == 1
    assert logs[0]["action"] == "login"
    assert logs[0]["details"] == "user admin"
    async with service.transaction() as session:
        stored = (await session.execute(select(AuditLog))).scalars().first()
        assert stored.correlation_id == cid
        assert stored.context_hash == hashlib.sha256(b"user admin").hexdigest()
        assert (
            Fernet(settings.audit_encryption_key)
            .decrypt(stored.context.encode())
            .decode()
            == "user admin"
        )


@pytest.mark.asyncio
async def test_insert_retry(monkeypatch) -> None:
    def fake_engine(url: str, **_: Any):
        return create_async_engine("sqlite+aiosqlite:///:memory:")

    monkeypatch.setattr(
        "database.services.database.create_async_engine",
        fake_engine,
    )
    settings = DatabaseSettings(
        url="postgresql+asyncpg://user:pass@localhost/test",
        encryption_key="8ZUJoRb_GXBDTPjL_Q0msBmE0vpo-hDabEIUkfGfs04=",
        audit_encryption_key="oh-tvfXPINv_kIWFlUufdfrwqcoYlEtp6SuMziSRVLI=",
        query_timeout=30,
    )
    service = DatabaseService(settings)
    async with service._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger = AsyncAuditLogger(service, settings.audit_encryption_key)
    attempts = {"c": 0}

    async def fail_then_pass(*args: Any, **kwargs: Any) -> None:
        if attempts["c"] < 1:
            attempts["c"] += 1
            raise RuntimeError("boom")
        await AsyncAuditLogger._save_batch(logger, *args, **kwargs)

    monkeypatch.setattr(logger, "_save_batch", fail_then_pass)
    logger._circuit = SimpleNamespace(call=lambda f, *a, **k: f(*a, **k))

    cid = await logger.insert_logs([("act", "d")], retries=2)
    assert attempts["c"] == 1
    logs = await logger.get_logs(cid)
    assert logs[0]["details"] == "d"
