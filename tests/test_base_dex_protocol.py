import asyncio
from unittest.mock import AsyncMock

import pytest

from dex_protocols.base import BaseDEXProtocol
from exceptions import DexError, ServiceUnavailableError


class DummyDEX(BaseDEXProtocol):
    async def _get_quote(self, token_in: str, token_out: str, amount_in: int) -> float:
        return 1.23

    async def _execute_swap(
        self, amount_in: int, route: list[str], amount_out_min: int
    ) -> str:
        return "0xdead"

    async def _get_best_route(
        self, token_in: str, token_out: str, amount_in: int
    ) -> list[str]:
        return ["a", "b"]


@pytest.mark.asyncio
async def test_methods_use_circuit_breaker(monkeypatch):
    dex = DummyDEX()
    async def call(func, *args, **kwargs):
        return await func(*args, **kwargs)
    call_mock = AsyncMock(side_effect=call)
    dex._circuit.call = call_mock
    price = await dex.get_quote("x", "y", 1)
    tx = await dex.execute_swap(1, ["x", "y"])
    route = await dex.get_best_route("x", "y", 1)
    assert price == 1.23
    assert tx == "0xdead"
    assert route == ["a", "b"]
    assert call_mock.await_count == 3
    assert call_mock.await_args_list[0].args[0] is not None


@pytest.mark.asyncio
async def test_execute_swap_raises_on_service_unavailable(monkeypatch):
    dex = DummyDEX()
    async def raise_unavailable(*_a, **_kw):
        raise ServiceUnavailableError("open")
    dex._circuit.call = AsyncMock(side_effect=raise_unavailable)
    with pytest.raises(DexError):
        await dex.execute_swap(1, ["a", "b"])


@pytest.mark.asyncio
async def test_validation_errors():
    dex = DummyDEX()
    with pytest.raises(DexError):
        await dex.get_quote("", "b", 1)
    with pytest.raises(DexError):
        await dex.execute_swap(0, [])
    with pytest.raises(DexError):
        await dex.get_best_route("a", "", -1)
