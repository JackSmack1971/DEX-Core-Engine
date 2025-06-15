import hashlib
from typing import Any

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import create_async_engine

from config import DatabaseSettings
from database.models import Base, AsyncFinancialAuditRecord
from database.services import DatabaseService


@pytest.mark.asyncio
async def test_financial_audit_record(monkeypatch) -> None:
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
    async with service.transaction() as session:
        record = AsyncFinancialAuditRecord(
            operation_type="deposit",
            data_encrypted="secret",
            hash=hashlib.sha256(b"secret").hexdigest(),
            correlation_id="cid1",
        )
        session.add(record)
        await session.flush()
        fetched = (
            await session.execute(select(AsyncFinancialAuditRecord))
        ).scalars().first()
        assert fetched is not None and fetched.operation_type == "deposit"
    async with service._engine.begin() as conn:
        indexes = await conn.run_sync(
            lambda c: inspect(c).get_indexes("async_financial_audit_record")
        )
    cols = {tuple(idx["column_names"]) for idx in indexes}
    assert ("created_at",) in cols
    assert ("correlation_id",) in cols
