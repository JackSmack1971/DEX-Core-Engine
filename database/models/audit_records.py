from __future__ import annotations

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import TimestampedModel


class AsyncFinancialAuditRecord(TimestampedModel):
    """Financial operation audit trail."""

    __tablename__ = "async_financial_audit_record"
    __table_args__ = (
        Index("ix_async_financial_audit_record_created_at", "created_at"),
        Index("ix_async_financial_audit_record_correlation_id", "correlation_id"),
    )

    operation_type: Mapped[str] = mapped_column(String(50))
    data_encrypted: Mapped[str] = mapped_column(String)
    hash: Mapped[str] = mapped_column(String(64))
    correlation_id: Mapped[str] = mapped_column(String(32))


__all__ = ["AsyncFinancialAuditRecord"]
