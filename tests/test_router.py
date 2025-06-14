from unittest.mock import AsyncMock, MagicMock

import pytest

from exceptions import DexError, ServiceUnavailableError, PriceManipulationError
from dex_protocols.base import LiquidityInfo
from slippage_protection import (
    MarketConditions,
    SlippageParams,
    SlippageProtectionEngine,
    MIN_TOLERANCE_PERCENT,
)
import routing
from routing import Router
from observability.metrics import SLIPPAGE_APPLIED, SLIPPAGE_VIOLATIONS


class DummyProto:
    def __init__(self, pools, name: str):
        self.pools = pools
        self.name = name
        self.get_quote = AsyncMock(return_value=100.0)
        self.execute_swap = AsyncMock(return_value=f"tx-{name}")
        service = MagicMock()
        service.web3.eth.gas_price = 1
        self.web3_service = service
        self.gas_limit = 1
        self.liq = LiquidityInfo(liquidity=100.0, price_impact=2.0)

    async def get_liquidity_info(self, *_: str) -> LiquidityInfo:
        return self.liq


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
async def test_execute_swap_delegates_to_adapters(monkeypatch):
    p1 = DummyProto([("a", "b", 1)], "p1")
    p2 = DummyProto([("b", "c", 1)], "p2")
    router = Router([p1, p2])
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "calculate_protected_slippage",
        lambda amt: max(1, int(amt) - 1),
    )
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "validate_transaction_slippage",
        lambda *_a, **_kw: None,
    )
    tx = await router.execute_swap(1, "a", "c")
    assert tx == "tx-p2"
    assert p1.execute_swap.await_count >= 1
    assert p2.execute_swap.await_count >= 1


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


@pytest.mark.asyncio
async def test_execute_split_on_high_slippage(monkeypatch):
    p1 = DummyProto([("a", "b", 1)], "p1")
    router = Router([p1])
    router.slippage_engine = SlippageProtectionEngine(SlippageParams(1.0, None))
    monkeypatch.setattr(
        router.slippage_engine,
        "get_market_conditions",
        AsyncMock(return_value=MarketConditions(100.0, 100.0, 0.0)),
    )
    p1.liq = LiquidityInfo(liquidity=100.0, price_impact=5.0)
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "calculate_protected_slippage",
        lambda amt: max(1, int(amt) - 1),
    )
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "validate_transaction_slippage",
        lambda *_a, **_kw: None,
    )
    await router.execute_swap(4, "a", "b")
    assert p1.execute_swap.await_count >= 2


@pytest.mark.asyncio
async def test_fallback_to_static_slippage(monkeypatch):
    p1 = DummyProto([("a", "b", 1)], "p1")
    router = Router([p1])
    router.slippage_engine = SlippageProtectionEngine(SlippageParams(1.0, None))

    async def fail() -> MarketConditions:
        raise ServiceUnavailableError("fail")

    monkeypatch.setattr(
        router.slippage_engine, "get_market_conditions", AsyncMock(side_effect=fail)
    )
    p1.liq = LiquidityInfo(liquidity=100.0, price_impact=0.0)
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "calculate_protected_slippage",
        lambda amt: max(1, int(amt) - 1),
    )
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "validate_transaction_slippage",
        lambda *_a, **_kw: None,
    )
    with pytest.raises(DexError):
        await router.execute_swap(2, "a", "b")
    assert p1.execute_swap.await_count == 0


@pytest.mark.asyncio
async def test_router_invokes_analysis(monkeypatch):
    p1 = DummyProto([("a", "b", 1)], "p1")
    router = Router([p1])
    engine = SlippageProtectionEngine(SlippageParams(1.0, None))
    router.slippage_engine = engine
    market = MarketConditions(100.0, 100.0, 0.2)
    called = {"count": 0}
    monkeypatch.setattr(engine, "get_market_conditions", AsyncMock(return_value=market))

    def _analyze(_: MarketConditions) -> str:
        called["count"] += 1
        return "stable"

    monkeypatch.setattr(engine, "analyze_market_conditions", _analyze)
    monkeypatch.setattr(
        routing.router,
        "calculate_dynamic_slippage",
        lambda impact, vol: 5.0,
    )
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "calculate_protected_slippage",
        lambda amt: max(1, int(amt) - 1),
    )
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "validate_transaction_slippage",
        lambda *_a, **_kw: None,
    )
    p1.liq = LiquidityInfo(liquidity=100.0, price_impact=0.1)
    await router.execute_swap(2, "a", "b")
    assert called["count"] >= 1
    assert p1.execute_swap.await_count >= 2


@pytest.mark.asyncio
async def test_reject_on_low_slippage(monkeypatch):
    p1 = DummyProto([("a", "b", 1)], "p1")
    router = Router([p1])
    router.slippage_engine = SlippageProtectionEngine(SlippageParams(1.0, None))
    p1.liq = LiquidityInfo(liquidity=100.0, price_impact=0.0)
    with pytest.raises(DexError):
        await router.execute_swap(1, "a", "b")


@pytest.mark.asyncio
async def test_router_slippage_metrics(monkeypatch):
    p1 = DummyProto([("a", "b", 1)], "p1")
    router = Router([p1])
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "calculate_protected_slippage",
        lambda amt: max(1, int(amt) - 1),
    )
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "validate_transaction_slippage",
        lambda *_a, **_kw: None,
    )
    start_sum = SLIPPAGE_APPLIED._sum.get()
    await router.execute_swap(1, "a", "b")
    assert SLIPPAGE_APPLIED._sum.get() > start_sum


@pytest.mark.asyncio
async def test_router_slippage_violation(monkeypatch):
    p1 = DummyProto([("a", "b", 1)], "p1")
    router = Router([p1])
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "calculate_protected_slippage",
        lambda amt: max(1, int(amt) - 1),
    )
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "validate_transaction_slippage",
        lambda *_a, **_kw: (_ for _ in ()).throw(PriceManipulationError("bad")),
    )
    start = SLIPPAGE_VIOLATIONS._value.get()
    with pytest.raises(DexError):
        await router.execute_swap(1, "a", "b")
    assert SLIPPAGE_VIOLATIONS._value.get() == start + 1


@pytest.mark.asyncio
async def test_router_zero_slippage_rejected(monkeypatch):
    p1 = DummyProto([("a", "b", 1)], "p1")
    router = Router([p1])
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "calculate_protected_slippage",
        lambda amt: amt,
    )
    call = {"count": 0}
    orig_validate = SlippageProtectionEngine.validate_transaction_slippage

    def _validate(expected: int, actual: int) -> None:
        call["count"] += 1
        orig_validate(expected, actual)

    monkeypatch.setattr(
        SlippageProtectionEngine,
        "validate_transaction_slippage",
        _validate,
    )
    with pytest.raises(DexError):
        await router.execute_swap(1, "a", "b")
    assert call["count"] == 1
    assert p1.execute_swap.await_count == 0
