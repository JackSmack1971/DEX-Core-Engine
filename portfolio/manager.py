from __future__ import annotations

from typing import Dict

from exceptions import InventoryError
from logger import get_logger
from risk_manager import RiskManager
from .assets import Asset, Portfolio
from .rebalancing import RebalancingEngine
from observability.metrics import PORTFOLIO_VALUE


class PortfolioManager(RiskManager):
    """Manage assets and perform rebalancing."""

    def __init__(self) -> None:
        super().__init__()
        self.portfolio = Portfolio()
        self.rebalancer = RebalancingEngine()
        self.logger = get_logger("portfolio_manager")

    def add_asset(self, symbol: str, amount: float, price: float) -> None:
        if amount < 0 or price <= 0:
            raise InventoryError("invalid amount or price")
        self.add_inventory(symbol, amount)
        self.set_price(symbol, price)
        self.portfolio.assets[symbol] = Asset(symbol, amount, price)
        PORTFOLIO_VALUE.set(self.portfolio.total_value())

    def update_price(self, symbol: str, price: float) -> None:
        self.set_price(symbol, price)
        asset = self.portfolio.assets.get(symbol)
        if asset:
            asset.price = price
        PORTFOLIO_VALUE.set(self.portfolio.total_value())

    async def rebalance(self, target: Dict[str, float]) -> None:
        await self.rebalancer.rebalance(self, target)
        PORTFOLIO_VALUE.set(self.portfolio.total_value())


__all__ = ["PortfolioManager"]
