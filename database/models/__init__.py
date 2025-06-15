"""Database ORM models export."""

from .base import Base, TimestampedModel
from .trading import MarketDataCache, StrategyPerformance, TradeExecution

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


class ConfigurationVersion(TimestampedModel):
    """Track configuration versions."""

    __tablename__ = "configuration_version"

    version: Mapped[str] = mapped_column(String(50), unique=True)


class UserSession(TimestampedModel):
    """Session information for platform users."""

    __tablename__ = "user_session"

    session_id: Mapped[str] = mapped_column(String(64), unique=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(TimestampedModel):
    """Record user and system actions."""

    __tablename__ = "audit_log"

    correlation_id: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[str] = mapped_column(String(100))
    context: Mapped[str] = mapped_column(String)
    context_hash: Mapped[str] = mapped_column(String(64))


class PortfolioSnapshot(TimestampedModel):
    """Snapshot of current portfolio state."""

    __tablename__ = "portfolio_snapshot"

    data: Mapped[str] = mapped_column(String)


class RiskEvent(TimestampedModel):
    """Risk-related events for auditing."""

    __tablename__ = "risk_event"

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

