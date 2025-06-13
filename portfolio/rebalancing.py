from __future__ import annotations

from typing import Dict

import config
from exceptions import InventoryError
from logger import get_logger
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async
from observability.metrics import REBALANCE_COUNT
from .assets import Asset


class RebalancingEngine:
    """Perform portfolio rebalancing with safety mechanisms."""

    def __init__(self) -> None:
        self.logger = get_logger("rebalancing_engine")
        self._circuit = CircuitBreaker()

    async def rebalance(self, manager: "PortfolioManager", target: Dict[str, float]) -> None:
        async def _rebalance() -> None:
            total = manager.portfolio.total_value()
            if total <= 0:
                return
            for symbol, weight in target.items():
                if weight < 0:
                    raise InventoryError("negative weight")
                asset = manager.portfolio.assets.get(symbol)
                if not asset:
                    continue
                desired = total * weight
                diff = abs(asset.value - desired) / total
                if diff < config.REBALANCE_THRESHOLD:
                    continue
                amount = desired / asset.price
                manager.inventory[symbol].balance = amount
                asset.amount = amount
        await self._circuit.call(retry_async, _rebalance)
        REBALANCE_COUNT.inc()


__all__ = ["RebalancingEngine"]
