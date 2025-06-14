"""Trading related ORM models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampedModel


class TradeExecution(TimestampedModel, Base):
    """Executed trade information."""

    __tablename__ = "trade_execution"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy: Mapped[str] = mapped_column(String(50), index=True)
    token_pair: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    tx_hash: Mapped[str] = mapped_column(String(66), unique=True)


class StrategyPerformance(TimestampedModel, Base):
    """Performance metrics for a trading strategy."""

    __tablename__ = "strategy_performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy: Mapped[str] = mapped_column(String(50), index=True)
    metric: Mapped[str] = mapped_column(String(50))
    value: Mapped[float] = mapped_column(Float)


class MarketDataCache(TimestampedModel, Base):
    """Cached market data for token pairs."""

    __tablename__ = "market_data_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_pair: Mapped[str] = mapped_column(String(50), index=True)
    data: Mapped[Any] = mapped_column(String)
