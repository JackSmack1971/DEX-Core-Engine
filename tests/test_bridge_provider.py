import pytest
from unittest.mock import AsyncMock
from exceptions import ServiceUnavailableError

from cross_chain.bridge_provider import HttpBridgeProvider, BridgeProviderError


class DummyClient:
    def __init__(self, data):
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url):
        return self

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


@pytest.mark.asyncio
async def test_get_price(monkeypatch):
    monkeypatch.setattr(
        "httpx.AsyncClient",
        lambda timeout=10: DummyClient({"price": 5.0}),
    )
    provider = HttpBridgeProvider("http://api")
    provider._circuit.call = lambda func, *a, **kw: func(*a, **kw)
    monkeypatch.setattr(
        "utils.retry.retry_async", lambda func, *a, **kw: func(*a, **kw)
    )
    price = await provider.get_price("token", "chain")
    assert price == 5.0


@pytest.mark.asyncio
async def test_get_price_error(monkeypatch):
    class FailClient(DummyClient):
        async def get(self, url):
            raise RuntimeError("fail")

    monkeypatch.setattr("httpx.AsyncClient", lambda timeout=10: FailClient({}))
    provider = HttpBridgeProvider("http://api")
    provider._circuit.call = lambda func, *a, **kw: func(*a, **kw)
    monkeypatch.setattr(
        "utils.retry.retry_async", lambda func, *a, **kw: func(*a, **kw)
    )
    with pytest.raises(BridgeProviderError):
        await provider.get_price("token", "chain")


@pytest.mark.asyncio
async def test_get_price_circuit_open(monkeypatch):
    provider = HttpBridgeProvider("http://api")
    provider._circuit.call = AsyncMock(
        side_effect=ServiceUnavailableError("open")
    )
    with pytest.raises(BridgeProviderError):
        await provider.get_price("token", "chain")
