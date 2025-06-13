import asyncio

import pytest
import config
from portfolio.manager import PortfolioManager
from observability.metrics import REBALANCE_COUNT


@pytest.mark.asyncio
async def test_rebalance_engine(monkeypatch):
    monkeypatch.setattr(config, "REBALANCE_THRESHOLD", 0.0)
    pm = PortfolioManager()
    pm.add_asset("A", 10, 1.0)
    pm.add_asset("B", 5, 2.0)
    start = REBALANCE_COUNT._value.get()
    await pm.rebalance({"A": 0.5, "B": 0.5})
    assert REBALANCE_COUNT._value.get() == start + 1
    total = pm.portfolio.total_value()
    assert abs(pm.portfolio.assets["A"].value - total / 2) < 1e-6
