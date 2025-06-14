import asyncio
from types import SimpleNamespace

import pytest

from cache.redis_cache import RedisCache, RedisCacheError


class DummyRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value

    async def get(self, key: str) -> str | None:
        return self.store.get(key)


class FailingRedis(DummyRedis):
    async def set(self, *args, **kwargs):
        raise ValueError("fail")

    async def get(self, key: str) -> str | None:
        raise ValueError("fail")


def _make_cache() -> RedisCache:
    cache = RedisCache()
    cache._client = DummyRedis()
    cache._circuit = SimpleNamespace(call=lambda f, *a, **k: f(*a, **k))
    return cache


@pytest.mark.asyncio
async def test_market_data_roundtrip() -> None:
    cache = _make_cache()
    await cache.set_market_data("ETH/USD", {"p": 1})
    assert await cache.get_market_data("ETH/USD") == {"p": 1}


@pytest.mark.asyncio
async def test_strategy_performance_roundtrip() -> None:
    cache = _make_cache()
    await cache.set_strategy_performance("s1", 2.5)
    assert await cache.get_strategy_performance("s1") == 2.5


@pytest.mark.asyncio
async def test_invalid_arguments() -> None:
    cache = _make_cache()
    with pytest.raises(RedisCacheError):
        await cache.set_market_data("", {})


@pytest.mark.asyncio
async def test_get_missing_returns_none() -> None:
    cache = _make_cache()
    assert await cache.get_strategy_performance("x") is None


@pytest.mark.asyncio
async def test_errors_wrapped() -> None:
    cache = RedisCache()
    cache._client = FailingRedis()
    cache._circuit = SimpleNamespace(call=lambda f, *a, **k: f(*a, **k))
    with pytest.raises(RedisCacheError):
        await cache.set_market_data("ETH/USD", {"p": 1})
    with pytest.raises(RedisCacheError):
        await cache.get_market_data("ETH/USD")
    with pytest.raises(RedisCacheError):
        await cache.set_strategy_performance("s", 1.0)
    with pytest.raises(RedisCacheError):
        await cache.get_strategy_performance("s")
