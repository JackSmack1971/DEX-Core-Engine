import pytest

from dex_protocols.base import LiquidityInfo
from risk_manager import PortfolioRiskManager, PortfolioSnapshot


class DummyProto:
    def __init__(self) -> None:
        self.liq = LiquidityInfo(liquidity=100.0, price_impact=0.0)

    async def get_liquidity_info(self, *_: str) -> LiquidityInfo:
        return self.liq


class DummyRouter:
    def __init__(self) -> None:
        self.proto = DummyProto()

    async def get_best_quote(
        self, token_in: str, token_out: str, amount_in: int
    ) -> float:
        return float(amount_in) * 2.0

    async def get_best_route(self, token_in: str, token_out: str, amount_in: int):
        return [self.proto], [token_in, token_out]


@pytest.mark.asyncio
async def test_update_price_history():
    router = DummyRouter()
    rm = PortfolioRiskManager(router)
    rm.add_inventory("a", 1)
    await rm.update_price_from_router("a", "b", 10)
    await rm.update_price_from_router("a", "b", 10)
    hist = list(rm.inventory["a"].price_history)
    assert hist[-1] == 2.0
    assert len(hist) == 2


def test_snapshot_contains_state():
    router = DummyRouter()
    rm = PortfolioRiskManager(router)
    rm.add_inventory("a", 1)
    rm.set_price("a", 1.0)
    snap = rm.snapshot()
    assert isinstance(snap, PortfolioSnapshot)
    assert snap.equity == rm.equity
    assert snap.inventory["a"].balance == 1


def test_risk_budget():
    router = DummyRouter()
    rm = PortfolioRiskManager(router, risk_budget=0.5)
    rm.add_inventory("a", 1)
    rm.set_price("a", 2.0)
    assert rm.check_risk_budget() is False


def test_concentration_check():
    router = DummyRouter()
    rm = PortfolioRiskManager(router, concentration_limit=0.4)
    rm.add_inventory("a", 1)
    rm.inventory["a"].allocation = 0.5
    assert rm.check_concentration() is False


@pytest.mark.asyncio
async def test_liquidity_check():
    router = DummyRouter()
    rm = PortfolioRiskManager(router, liquidity_threshold=0.1)
    assert await rm.check_liquidity("a", "b", 50) is True
    router.proto.liq = LiquidityInfo(liquidity=1.0, price_impact=0.0)
    assert await rm.check_liquidity("a", "b", 50) is False
