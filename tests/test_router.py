from unittest.mock import AsyncMock, MagicMock

import pytest

from exceptions import DexError
from routing import Router


class DummyProto:
    def __init__(self, pools, name: str):
        self.pools = pools
        self.name = name
        self.get_quote = AsyncMock(return_value=1.0)
        self.execute_swap = AsyncMock(return_value=f"tx-{name}")
        service = MagicMock()
        service.web3.eth.gas_price = 1
        self.web3_service = service
        self.gas_limit = 1


@pytest.mark.asyncio
async def test_multi_hop_route_selection():
    p1 = DummyProto([("a", "b", 1)], "p1")
    p2 = DummyProto([("b", "c", 1)], "p2")
    p3 = DummyProto([("a", "c", 5)], "p3")
    router = Router([p1, p2, p3])

    protos, route = await router.get_best_route("a", "c", 1)
    assert route == ["a", "b", "c"]
    assert protos == [p1, p2]


@pytest.mark.asyncio
async def test_execute_swap_delegates_to_adapters():
    p1 = DummyProto([("a", "b", 1)], "p1")
    p2 = DummyProto([("b", "c", 1)], "p2")
    router = Router([p1, p2])
    tx = await router.execute_swap(1, "a", "c")
    assert tx == "tx-p2"
    assert p1.execute_swap.await_count == 1
    assert p2.execute_swap.await_count == 1


@pytest.mark.asyncio
async def test_no_liquidity_raises_error():
    p1 = DummyProto([], "p1")
    router = Router([p1])
    with pytest.raises(DexError):
        await router.get_best_route("a", "b", 1)


@pytest.mark.asyncio
async def test_route_cache(monkeypatch):
    p1 = DummyProto([("a", "b", 1)], "p1")
    router = Router([p1])
    monkeypatch.setattr(router, "_current_block", lambda: 1)
    path_mock = MagicMock(return_value=([p1], ["a", "b"]))
    router._shortest_path = path_mock
    await router.get_best_route("a", "b", 1)
    await router.get_best_route("a", "b", 1)
    assert path_mock.call_count == 1
    monkeypatch.setattr(router, "_current_block", lambda: 2)
    await router.get_best_route("a", "b", 1)
    assert path_mock.call_count == 2

