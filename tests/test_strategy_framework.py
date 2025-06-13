from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest

from strategies.base import BaseStrategy, StrategyConfig
from strategies.registry import StrategyRegistry
from strategies.arbitrage import ArbitrageStrategy


class DummyStrategy(BaseStrategy):
    async def analyze_market(self) -> Dict[str, Any]:
        return {}

    async def generate_signals(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def execute_trades(self, signals: List[Dict[str, Any]]) -> List[str]:
        return []


@pytest.mark.asyncio
async def test_registry_create_strategy():
    registry = StrategyRegistry()
    registry.register("dummy", DummyStrategy)
    strat = registry.create_strategy("dummy", router=None, config=StrategyConfig(name="dummy"))
    assert isinstance(strat, DummyStrategy)
    assert "dummy" in registry.list_strategies()


@pytest.mark.asyncio
async def test_arbitrage_run_cycle(monkeypatch):
    router = type("R", (), {})()
    router.get_best_quote = AsyncMock(return_value=1.0)
    strategy = ArbitrageStrategy(router)
    await strategy.run_cycle()
    assert strategy.metrics.total_trades >= 0
