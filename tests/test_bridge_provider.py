import pytest
from unittest.mock import AsyncMock
import httpx
from exceptions import ServiceUnavailableError

from cross_chain.bridge_provider import HttpBridgeProvider, BridgeProviderError


class DummyClient:
    def __init__(self, data):
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url, timeout=10):
        return self

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


@pytest.mark.asyncio
async def test_get_price(monkeypatch):
    client_factory = lambda: DummyClient({"price": 5.0})
    monkeypatch.setattr("httpx.AsyncClient", client_factory)
    provider = HttpBridgeProvider("http://api")
    provider._circuit.call = lambda func, *a, **kw: func(*a, **kw)
    patch_retry = lambda func, *a, **kw: func(*a, **kw)
    monkeypatch.setattr("utils.retry.retry_async", patch_retry)
    price = await provider.get_price("token", "chain")
    assert price == 5.0


@pytest.mark.asyncio
async def test_get_price_error(monkeypatch):
    class FailClient(DummyClient):
        async def get(self, url, timeout=10):
            raise httpx.RequestError("fail", request=httpx.Request("GET", url))

    monkeypatch.setattr("httpx.AsyncClient", lambda: FailClient({}))
    provider = HttpBridgeProvider("http://api")
    provider._circuit.call = lambda func, *a, **kw: func(*a, **kw)
    patch_retry = lambda func, *a, **kw: func(*a, **kw)
    monkeypatch.setattr("utils.retry.retry_async", patch_retry)
    with pytest.raises(BridgeProviderError):
        await provider.get_price("token", "chain")


@pytest.mark.asyncio
async def test_get_price_transient_failure(monkeypatch):
    class FlakyClient(DummyClient):
        def __init__(self) -> None:
            super().__init__({"price": 7.0})
            self.calls = 0

        async def get(self, url, timeout=10):
            if self.calls == 0:
                self.calls += 1
                raise httpx.RequestError(
                    "fail", request=httpx.Request("GET", url)
                )
            return self

    async def fake_retry(func, *args, retries=3, **kwargs):
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except Exception:
                if attempt == retries - 1:
                    raise

    monkeypatch.setattr("httpx.AsyncClient", lambda: FlakyClient())
    monkeypatch.setattr("utils.retry.retry_async", fake_retry)
    provider = HttpBridgeProvider("http://api")
    provider._circuit.call = lambda func, *a, **kw: func(*a, **kw)
    price = await provider.get_price("token", "chain")
    assert price == 7.0


@pytest.mark.asyncio
async def test_get_price_circuit_open(monkeypatch):
    provider = HttpBridgeProvider("http://api")
    provider._circuit.call = AsyncMock(
        side_effect=ServiceUnavailableError("open")
    )
    with pytest.raises(BridgeProviderError):
        await provider.get_price("token", "chain")


@pytest.mark.asyncio
async def test_get_price_request_error(monkeypatch):
    class FailingClient(DummyClient):
        async def get(self, url, timeout=10):
            raise httpx.RequestError("boom", request=httpx.Request("GET", url))

    async def fake_retry(func, *args, retries=3, **kwargs):
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except Exception:
                if attempt == retries - 1:
                    raise

    monkeypatch.setattr("httpx.AsyncClient", lambda: FailingClient({}))
    monkeypatch.setattr("utils.retry.retry_async", fake_retry)
    provider = HttpBridgeProvider("http://api")
    provider._circuit.call = lambda func, *a, **kw: func(*a, **kw)
    with pytest.raises(BridgeProviderError):
        await provider.get_price("token", "chain")
