"""Repository for trade execution models."""

from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TradeExecution
from .base import BaseRepository


class TradeRepository(BaseRepository):
    """Operations for persisting and querying trades."""

    async def record_trade(self, trade: TradeExecution) -> None:
        self._session.add(trade)
        await self._session.flush()

    async def get_strategy_trades(self, strategy: str) -> List[TradeExecution]:
        stmt = select(TradeExecution).where(TradeExecution.strategy == strategy)
        result = await self._session.execute(stmt)
        return list(result.scalars())

