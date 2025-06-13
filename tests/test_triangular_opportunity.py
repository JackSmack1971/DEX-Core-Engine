import pytest
from unittest.mock import AsyncMock, MagicMock

from cross_chain.bridge_provider import BridgeProvider
from strategies.arbitrage_engine import (
    ArbitrageType,
    OpportunityDetector,
)
from routing import Router
from dex_protocols.base import LiquidityInfo


class DummyProvider(BridgeProvider):
    def __init__(self) -> None:
        super().__init__("http://test")

    async def get_price(self, token: str, chain: str) -> float:
        return 0.0


class DummyProto:
    def __init__(self, pools, name: str):
        self.pools = pools
        self.name = name
        self.get_quote = AsyncMock(return_value=1.1)
        self.execute_swap = AsyncMock(return_value=f"tx-{name}")
        service = MagicMock()
        service.web3.eth.gas_price = 0
        self.web3_service = service
        self.gas_limit = 0
        self.liq = LiquidityInfo(liquidity=100.0, price_impact=0.0)

    async def get_liquidity_info(self, *_: str) -> LiquidityInfo:
        return self.liq


@pytest.mark.asyncio
async def test_detector_triangular_cycle():
    p1 = DummyProto([("a", "b", 0)], "p1")
    p2 = DummyProto([("b", "c", 0)], "p2")
    p3 = DummyProto([("c", "a", 0)], "p3")
    router = Router([p1, p2, p3])
    router.slippage_engine = None
    detector = OpportunityDetector(router, ["a", "b", "c"], amount=1, providers=[DummyProvider()])
    opps = await detector.scan()
    assert any(o.opportunity_type is ArbitrageType.TRIANGULAR for o in opps)
