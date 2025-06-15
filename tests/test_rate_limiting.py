import asyncio
import time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "security.rate_limiting", Path("security/rate_limiting.py")
)
rate_limiting = importlib.util.module_from_spec(spec)
sys.modules["security.rate_limiting"] = rate_limiting
assert spec.loader is not None
spec.loader.exec_module(rate_limiting)
from exceptions import RateLimitError


class DummyRedis:
    def __init__(self) -> None:
        self.store: dict[str, int] = {}
        self.expiry: dict[str, float] = {}

    async def incr(self, key: str) -> int:
        if key in self.expiry and self.expiry[key] <= time.time():
            self.store.pop(key, None)
            self.expiry.pop(key, None)
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    async def expire(self, key: str, seconds: int) -> None:
        self.expiry[key] = time.time() + seconds


def _patch_client(monkeypatch: pytest.MonkeyPatch, client: DummyRedis) -> None:
    monkeypatch.setattr(rate_limiting, "get_redis", lambda: client)


def test_check_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    client = DummyRedis()
    _patch_client(monkeypatch, client)
    asyncio.run(rate_limiting.check_rate_limit("u", "s", 2, 1))
    asyncio.run(rate_limiting.check_rate_limit("u", "s", 2, 1))
    assert client.store["rl:u:s"] == 2


def test_rate_limit_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    client = DummyRedis()
    _patch_client(monkeypatch, client)
    asyncio.run(rate_limiting.check_rate_limit("u", "s", 1, 1))
    with pytest.raises(RateLimitError):
        asyncio.run(rate_limiting.check_rate_limit("u", "s", 1, 1))


def test_rate_limit_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    client = DummyRedis()
    _patch_client(monkeypatch, client)
    asyncio.run(rate_limiting.check_rate_limit("u", "s", 1, 1))
    time.sleep(1.1)
    asyncio.run(rate_limiting.check_rate_limit("u", "s", 1, 1))
    assert client.store["rl:u:s"] == 1


def test_decorator(monkeypatch: pytest.MonkeyPatch) -> None:
    client = DummyRedis()
    _patch_client(monkeypatch, client)

    @rate_limiting.rate_limit("s", 1, 1)
    async def handler(current_user):
        return "ok"

    user = SimpleNamespace(username="u")
    assert asyncio.run(handler(current_user=user)) == "ok"
    with pytest.raises(HTTPException) as exc:
        asyncio.run(handler(current_user=user))
    assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_async_rate_limit_enforcement(monkeypatch: pytest.MonkeyPatch) -> None:
    client = DummyRedis()
    _patch_client(monkeypatch, client)
    await rate_limiting.check_rate_limit("u", "scope", 1, 1)
    with pytest.raises(RateLimitError):
        await rate_limiting.check_rate_limit("u", "scope", 1, 1)


@pytest.mark.asyncio
async def test_async_decorator(monkeypatch: pytest.MonkeyPatch) -> None:
    client = DummyRedis()
    _patch_client(monkeypatch, client)

    @rate_limiting.rate_limit("scope", 1, 1)
    async def handler(current_user):
        return "ok"

    user = SimpleNamespace(username="u")
    assert await handler(current_user=user) == "ok"
    with pytest.raises(HTTPException):
        await handler(current_user=user)
