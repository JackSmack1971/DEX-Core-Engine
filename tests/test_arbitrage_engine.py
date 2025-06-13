import asyncio
from typing import List
from unittest.mock import AsyncMock

import pytest

from strategies.arbitrage_engine import (
    ArbitrageEngine,
    ArbitrageOpportunity,
    ArbitrageType,
    OpportunityDetector,
)
class DummyRouter:
    def __init__(self) -> None:
        self.get_best_quote = AsyncMock(side_effect=[1.1, 1.2])
        self.execute_swap = AsyncMock(return_value="0xtx")


@pytest.mark.asyncio
async def test_detector_finds_opportunity():
    router = DummyRouter()
    detector = OpportunityDetector(router, ["a", "b"], amount=1)
    opps = await detector.scan()
    assert opps
    assert opps[0].opportunity_type is ArbitrageType.SIMPLE


@pytest.mark.asyncio
async def test_engine_executes_trade():
    router = DummyRouter()
    engine = ArbitrageEngine(router, tokens=["a", "b"])
    market = await engine.analyze_market()
    signals = await engine.generate_signals(market)
    txs = await engine.execute_trades(signals)
    assert txs == ["0xtx"]
