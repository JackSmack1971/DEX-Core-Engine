from pathlib import Path
from types import SimpleNamespace

import pytest

from database.scripts import backup, maintenance
from exceptions import ConfigurationError


@pytest.mark.asyncio
async def test_run_backup(monkeypatch, tmp_path):
    out = tmp_path / "db.sql"

    async def fake_exec(dsn: str, path: Path, timeout: int) -> None:
        path.write_text("content")

    monkeypatch.setattr(backup, "_exec_pg_dump", fake_exec)
    enc = await backup.run_backup(str(out))
    assert enc.exists()
    assert enc.suffix == ".enc"


@pytest.mark.asyncio
async def test_run_backup_missing_env(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE__URL", raising=False)
    with pytest.raises(ConfigurationError):
        await backup.run_backup(str(tmp_path / "out.sql"))


@pytest.mark.asyncio
async def test_vacuum_and_index(monkeypatch):
    executed: list[str] = []

    class Conn:
        async def execute(self, query: str) -> None:
            executed.append(query)

        async def fetch(self, query: str):
            return [dict(name="idx")]

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def fake_connect(_):
        return Conn()

    monkeypatch.setattr(
        maintenance,
        "asyncpg",
        SimpleNamespace(connect=fake_connect),
    )
    monkeypatch.setattr(
        maintenance,
        "retry_async",
        lambda func, *a, **k: func(*a, **k),
    )

    await maintenance.vacuum_analyze()
    assert executed == ["VACUUM (ANALYZE)"]
    res = await maintenance.check_indexes()
    assert res == ["idx"]
