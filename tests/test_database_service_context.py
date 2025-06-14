import pytest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any

from sqlalchemy.ext.asyncio import create_async_engine
from observability.metrics import DB_HEALTH_FAILURES

from exceptions import ServiceUnavailableError
from database.services import DatabaseService
from config import DatabaseSettings
from database.models import Base


class DummyFailSession:
    def __init__(self) -> None:
        self.closed = False

    async def execute(self, *args: Any, **kwargs: Any):
        raise RuntimeError("boom")

    async def rollback(self) -> None:
        pass

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_get_session_failure(monkeypatch) -> None:
    def fake_engine(url: str, **kwargs: Any):
        return create_async_engine("sqlite+aiosqlite:///:memory:")

    monkeypatch.setattr(
        "database.services.database.create_async_engine",
        fake_engine,
    )
    service = DatabaseService(
        DatabaseSettings(url="postgresql+asyncpg://user:pass@localhost/test")
    )
    dummy = DummyFailSession()
    service._sessionmaker = lambda: dummy
    service._circuit = SimpleNamespace(call=lambda f, *a, **k: f(*a, **k))
    failures_before = DB_HEALTH_FAILURES._value.get()
    with pytest.raises(ServiceUnavailableError):
        async with service.get_session():
            pass
    assert dummy.closed
    assert DB_HEALTH_FAILURES._value.get() == failures_before + 1
