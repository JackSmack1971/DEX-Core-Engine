"""Database ORM models export."""

from .base import Base, TimestampedModel
from .trading import MarketDataCache, StrategyPerformance, TradeExecution

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class ConfigurationVersion(TimestampedModel, Base):
    """Track configuration versions."""

    __tablename__ = "configuration_version"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(50), unique=True)


class UserSession(TimestampedModel, Base):
    """Session information for platform users."""

    __tablename__ = "user_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(TimestampedModel, Base):
    """Record user and system actions."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(100))
    context: Mapped[str] = mapped_column(String)


class PortfolioSnapshot(TimestampedModel, Base):
    """Snapshot of current portfolio state."""

    __tablename__ = "portfolio_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data: Mapped[str] = mapped_column(String)


class RiskEvent(TimestampedModel, Base):
    """Risk-related events for auditing."""

    __tablename__ = "risk_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String)


__all__ = [
    "Base",
    "TimestampedModel",
    "TradeExecution",
    "StrategyPerformance",
    "MarketDataCache",
    "ConfigurationVersion",
    "UserSession",
    "AuditLog",
    "PortfolioSnapshot",
    "RiskEvent",
]

