from unittest.mock import AsyncMock

import pytest

from exceptions import DexError
from routing import Router


class DummyProto:
    def __init__(self, quote: float, name: str = "proto"):
        self.quote = quote
        self.name = name
        self.get_best_route = AsyncMock(return_value=["a", "b"])
        self.get_quote = AsyncMock(return_value=quote)
        self.execute_swap = AsyncMock(return_value=f"tx-{name}")


@pytest.mark.asyncio
async def test_get_best_route_selects_highest_quote():
    p1 = DummyProto(1.0, "p1")
    p2 = DummyProto(2.0, "p2")
    router = Router([p1, p2])

    proto, route = await router.get_best_route("a", "b", 1)
    assert proto is p2
    assert route == ["a", "b"]


@pytest.mark.asyncio
async def test_execute_swap_delegates_to_adapter():
    p1 = DummyProto(1.0, "p1")
    router = Router([p1])
    tx = await router.execute_swap(1, "a", "b")
    assert tx == "tx-p1"
    p1.execute_swap.assert_awaited_once()


@pytest.mark.asyncio
async def test_no_liquidity_raises_error():
    p1 = DummyProto(0.0)
    router = Router([p1])
    with pytest.raises(DexError):
        await router.get_best_route("a", "b", 1)
