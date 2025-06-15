"""Asynchronous audit logging with encryption and hashing."""

from __future__ import annotations

import hashlib
from typing import Iterable, List, Sequence

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AuditLog
from database.services import DatabaseService
from exceptions import DatabaseError
from logger import get_logger, set_correlation_id
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async


class AsyncAuditLogger:
    """Persist encrypted audit records with correlation IDs."""

    def __init__(self, db: DatabaseService, encryption_key: str) -> None:
        if len(encryption_key) != 44:
            raise ValueError("invalid Fernet key")
        self._db = db
        self._fernet = Fernet(encryption_key)
        self.logger = get_logger("audit_logger")
        self._circuit = CircuitBreaker()

    def _encrypt(self, detail: str) -> tuple[str, str]:
        data = detail.encode()
        return (
            self._fernet.encrypt(data).decode(),
            hashlib.sha256(data).hexdigest(),
        )

    def _decrypt(self, data: str) -> str:
        return self._fernet.decrypt(data.encode()).decode()

    async def _save_batch(self, records: Sequence[AuditLog]) -> None:
        async with self._db.transaction() as session:
            session.add_all(list(records))
            await session.flush()

    async def insert_logs(
        self,
        entries: Iterable[tuple[str, str]],
        correlation_id: str | None = None,
        retries: int = 3,
    ) -> str:
        cid = set_correlation_id(correlation_id)
        records: List[AuditLog] = []
        for action, detail in entries:
            if not action or not detail:
                raise DatabaseError("invalid log entry")
            enc, digest = self._encrypt(detail)
            records.append(
                AuditLog(
                    correlation_id=cid,
                    action=action,
                    context=enc,
                    context_hash=digest,
                )
            )

        async def _op() -> None:
            await self._save_batch(records)

        try:
            await self._circuit.call(
                retry_async, _op, retries=retries
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Insert logs failed: %s", exc)
            raise DatabaseError("audit insert failure") from exc
        return cid

    async def get_logs(
        self,
        correlation_id: str | None = None,
        limit: int | None = None,
        retries: int = 3,
    ) -> List[dict]:
        async def _op(session: AsyncSession) -> List[AuditLog]:
            stmt = select(AuditLog)
            if correlation_id:
                stmt = stmt.where(AuditLog.correlation_id == correlation_id)
            if limit:
                stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars())

        async def _fetch() -> List[AuditLog]:
            async with self._db.transaction() as session:
                return await _op(session)

        try:
            records = await self._circuit.call(
                retry_async, _fetch, retries=retries
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Fetch logs failed: %s", exc)
            raise DatabaseError("audit fetch failure") from exc

        return [
            {
                "action": r.action,
                "details": self._decrypt(r.context),
                "correlation_id": r.correlation_id,
                "hash": r.context_hash,
            }
            for r in records
        ]


__all__ = ["AsyncAuditLogger"]
