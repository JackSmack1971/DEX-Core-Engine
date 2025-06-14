"""Trading related ORM models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import TimestampedModel


class TradeExecution(TimestampedModel):
    """Executed trade information."""

    __tablename__ = "trade_execution"

    strategy: Mapped[str] = mapped_column(String(50), index=True)
    token_pair: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    tx_hash: Mapped[str] = mapped_column(String(66), unique=True)


class StrategyPerformance(TimestampedModel):
    """Performance metrics for a trading strategy."""

    __tablename__ = "strategy_performance"

    strategy: Mapped[str] = mapped_column(String(50), index=True)
    metric: Mapped[str] = mapped_column(String(50))
    value: Mapped[float] = mapped_column(Float)


class MarketDataCache(TimestampedModel):
    """Cached market data for token pairs."""

    __tablename__ = "market_data_cache"

    token_pair: Mapped[str] = mapped_column(String(50), index=True)
    data: Mapped[Any] = mapped_column(String)
