from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TradeExecution


class TradeRepository:
    """Repository for trade execution data."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_trade(self, trade: TradeExecution) -> None:
        self._session.add(trade)
        await self._session.flush()

    async def get_strategy_trades(self, strategy: str) -> List[TradeExecution]:
        stmt = select(TradeExecution).where(TradeExecution.strategy == strategy)
        res = await self._session.execute(stmt)
        return list(res.scalars())

