"""Base repository providing session access."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Common repository utilities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

