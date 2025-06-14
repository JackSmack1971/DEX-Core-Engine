import asyncio

import pytest

from database.service import DatabaseService
from config import CONFIG_MANAGER


@pytest.mark.asyncio
async def test_get_session():
    service = DatabaseService(CONFIG_MANAGER.config.database)
    async with service.transaction() as session:
        assert session.bind


from database.models import Base, TradeExecution
from database.repositories.trade_repository import TradeRepository


@pytest.mark.asyncio
async def test_trade_repository_record_and_get():
    service = DatabaseService(CONFIG_MANAGER.config.database)
    async with service.transaction() as session:
        async with service._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        repo = TradeRepository(session)
        trade = TradeExecution(strategy="s1", token_pair="A/B", amount=1.0, price=2.0, tx_hash="0x1")
        await repo.record_trade(trade)
        result = await repo.get_strategy_trades("s1")
        assert len(result) == 1
        assert result[0].tx_hash == "0x1"
