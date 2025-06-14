import asyncio
from typing import Any

import pytest

from database.services import DatabaseService
from sqlalchemy.ext.asyncio import create_async_engine
from config import CONFIG_MANAGER, DatabaseSettings
from observability.metrics import (
    DB_ACTIVE_CONNECTIONS,
    DB_HEALTH_CHECKS,
    DB_HEALTH_FAILURES,
)


@pytest.mark.asyncio
async def test_get_session(monkeypatch):
    def fake_engine(url: str, **kwargs: Any):
        return create_async_engine("sqlite+aiosqlite:///:memory:")

    monkeypatch.setattr(
        "database.services.database.create_async_engine", fake_engine
    )
    settings = DatabaseSettings(
        url="postgresql+asyncpg://user:pass@localhost/test"
    )
    service = DatabaseService(settings)
    start_checks = DB_HEALTH_CHECKS._value.get()
    async with service.transaction() as session:
        assert session.bind
        assert DB_ACTIVE_CONNECTIONS._value.get() > 0
    assert DB_ACTIVE_CONNECTIONS._value.get() == 0
    assert DB_HEALTH_CHECKS._value.get() == start_checks + 1
    assert DB_HEALTH_FAILURES._value.get() == 0


from database.models import Base, TradeExecution
from database.repositories import TradeRepository


@pytest.mark.asyncio
async def test_trade_repository_record_and_get(monkeypatch):
    def fake_engine(url: str, **kwargs: Any):
        return create_async_engine("sqlite+aiosqlite:///:memory:")

    monkeypatch.setattr(
        "database.services.database.create_async_engine", fake_engine
    )
    settings = DatabaseSettings(
        url="postgresql+asyncpg://user:pass@localhost/test"
    )
    service = DatabaseService(settings)
    async with service.transaction() as session:
        async with service._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        repo = TradeRepository(session)
        trade = TradeExecution(strategy="s1", token_pair="A/B", amount=1.0, price=2.0, tx_hash="0x1")
        await repo.record_trade(trade)
        result = await repo.get_strategy_trades("s1")
        assert len(result) == 1
        assert result[0].tx_hash == "0x1"
