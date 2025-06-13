"""Risk management utilities for trading."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Any
import time
import copy

import config
from exceptions import InventoryError, StrategyError
from logger import get_logger
from routing import Router


logger = get_logger("risk_manager")


@dataclass
class Position:
    """Simple trade position."""

    entry_price: float
    size: float
    stop_loss: float
    take_profit: float


@dataclass
class InventoryItem:
    """Track token balance and valuation."""

    balance: float = 0.0
    price: float = 0.0
    price_history: Deque[float] = field(
        default_factory=lambda: deque(maxlen=100)
    )
    allocation: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def value(self) -> float:
        return self.balance * self.price


@dataclass
class PortfolioSnapshot:
    """Timestamped snapshot of portfolio state."""

    timestamp: float
    equity: float
    inventory: Dict[str, InventoryItem]
    positions: List[Position]


class RiskManager:
    """Evaluate and track trade risk.

    Environment variables used:
        MAX_DRAWDOWN_PERCENT, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT
    """

    def __init__(self) -> None:
        self.max_drawdown = config.MAX_DRAWDOWN_PERCENT / 100
        self.stop_loss_pct = config.STOP_LOSS_PERCENT / 100
        self.take_profit_pct = config.TAKE_PROFIT_PERCENT / 100
        self.equity = 1.0
        self.high_water = self.equity
        self.positions: List[Position] = []
        self.returns: Deque[float] = deque(maxlen=100)
        self.inventory: Dict[str, InventoryItem] = {}

    def position_size(self, balance: float, risk_per_trade: float) -> float:
        """Compute position size using fixed fractional/Kelly."""
        if risk_per_trade <= 0:
            raise StrategyError("risk_per_trade must be positive")
        edge = risk_per_trade
        kelly = edge / 1  # assume payoff 1:1
        frac = min(config.RISK_LIMIT, kelly)
        size = balance * frac
        logger.info("Position size %.4f", size)
        return min(size, config.MAX_POSITION_SIZE)

    def update_equity(self, pnl: float) -> None:
        """Record profit or loss."""
        self.equity += pnl
        self.high_water = max(self.high_water, self.equity)
        self.returns.append(pnl)
        logger.debug("Equity updated to %.4f", self.equity)

    def check_drawdown(self) -> bool:
        """Return True if drawdown exceeds limit."""
        dd = 1 - self.equity / self.high_water
        if dd >= self.max_drawdown:
            logger.error("Drawdown %.2f exceeded", dd)
            return True
        return False

    def add_position(self, price: float, balance: float, risk: float) -> Position:
        """Create and track a new position."""
        size = self.position_size(balance, risk)
        stop = price * (1 - self.stop_loss_pct)
        take = price * (1 + self.take_profit_pct)
        pos = Position(price, size, stop, take)
        self.positions.append(pos)
        logger.info("Position opened at %.2f size %.4f", price, size)
        return pos

    def monitor(self, price: float) -> List[Position]:
        """Check open positions against stops."""
        closed: List[Position] = []
        remaining: List[Position] = []
        for pos in self.positions:
            if price <= pos.stop_loss or price >= pos.take_profit:
                pnl = (price - pos.entry_price) * pos.size
                self.update_equity(pnl)
                closed.append(pos)
                logger.warning("Position closed at %.2f", price)
            else:
                remaining.append(pos)
        self.positions = remaining
        return closed

    def add_inventory(self, token: str, amount: float) -> None:
        """Increase inventory for ``token``."""
        if amount < 0:
            raise InventoryError("amount must be non-negative")
        item = self.inventory.get(token)
        if item is None:
            self.inventory[token] = InventoryItem(balance=amount)
        else:
            item.balance += amount

    def remove_inventory(self, token: str, amount: float) -> None:
        """Decrease inventory for ``token``."""
        if amount < 0:
            raise InventoryError("amount must be non-negative")
        item = self.inventory.get(token)
        if not item or item.balance < amount:
            raise InventoryError("insufficient inventory")
        item.balance -= amount

    def get_inventory(self, token: str) -> float:
        """Return stored amount of ``token``."""
        item = self.inventory.get(token)
        return item.balance if item else 0.0

    def set_price(self, token: str, price: float) -> None:
        """Update tracked price for ``token``."""
        if price <= 0:
            raise InventoryError("price must be positive")
        item = self.inventory.get(token)
        if item is None:
            self.inventory[token] = InventoryItem(price=price)
            item = self.inventory[token]
        else:
            item.price = price
        item.price_history.append(price)

    def inventory_value(self) -> float:
        """Return total inventory valuation."""
        return sum(item.value for item in self.inventory.values())

    def rebalance_inventory(self, token0: str, token1: str, target_ratio: float) -> None:
        """Rebalance two tokens to achieve desired value ratio."""
        if target_ratio <= 0:
            raise InventoryError("target_ratio must be positive")
        item0 = self.inventory.get(token0)
        item1 = self.inventory.get(token1)
        if not item0 or not item1:
            raise InventoryError("tokens missing")
        total = item0.value + item1.value
        desired0 = total * target_ratio / (1 + target_ratio)
        desired1 = total - desired0
        item0.balance = desired0 / item0.price
        item1.balance = desired1 / item1.price

    def hedge_impermanent_loss(
        self, token0: str, token1: str, initial_price: float, current_price: float
    ) -> float:
        """Hedge impermanent loss by rebalancing inventory."""
        loss = self.impermanent_loss(
            initial_price,
            current_price,
            self.get_inventory(token0),
            self.get_inventory(token1),
        )
        self.rebalance_inventory(token0, token1, 1.0)
        return loss

    def impermanent_loss(
        self, initial_price: float, current_price: float, amount0: float, amount1: float
    ) -> float:
        """Estimate impermanent loss given price change."""
        if initial_price <= 0 or current_price <= 0:
            raise InventoryError("prices must be positive")
        if amount0 < 0 or amount1 < 0:
            raise InventoryError("amounts must be non-negative")
        ratio = current_price / initial_price
        hodl_value = amount0 + amount1 * ratio
        lp_value = 2 * math.sqrt(ratio) / (1 + ratio) * hodl_value
        return hodl_value - lp_value

    def var(self, confidence: float = 0.95) -> float:
        """Compute simple historical VaR."""
        if not self.returns:
            return 0.0
        sorted_r = sorted(self.returns)
        idx = max(0, int((1 - confidence) * len(sorted_r)) - 1)
        return abs(sorted_r[idx])

    def sharpe(self) -> float:
        """Calculate annualized Sharpe ratio."""
        if not self.returns:
            return 0.0
        avg = sum(self.returns) / len(self.returns)
        var = sum((r - avg) ** 2 for r in self.returns) / len(self.returns)
        std = math.sqrt(var)
        if std == 0:
            return 0.0
        return (avg / std) * math.sqrt(len(self.returns))

    def shutdown(self) -> None:
        """Close all positions."""
        for pos in list(self.positions):
            self.update_equity((0 - pos.entry_price) * pos.size)
        self.positions.clear()
        logger.critical("Emergency shutdown activated")


class PortfolioRiskManager(RiskManager):
    """Risk management with portfolio-level checks."""

    def __init__(
        self,
        router: "Router",
        risk_budget: float = 1.0,
        liquidity_threshold: float = 0.1,
        concentration_limit: float = 0.5,
    ) -> None:
        super().__init__()
        self.router = router
        self.risk_budget = risk_budget
        self.liquidity_threshold = liquidity_threshold
        self.concentration_limit = concentration_limit
        self.logger = get_logger("portfolio_risk_manager")

    async def update_price_from_router(
        self, token: str, base: str, amount: int
    ) -> None:
        if amount <= 0:
            raise InventoryError("amount must be positive")
        try:
            quote = await self.router.get_best_quote(token, base, amount)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Price fetch failed: %s", exc)
            raise InventoryError(str(exc)) from exc
        price = quote / float(amount)
        self.set_price(token, price)

    def check_risk_budget(self) -> bool:
        allowed = self.equity * self.risk_budget
        total = self.inventory_value()
        if total > allowed:
            self.logger.warning("Risk budget breached: %.4f > %.4f", total, allowed)
            return False
        return True

    async def check_liquidity(
        self, token: str, base: str, amount: int
    ) -> bool:
        try:
            protos, route = await self.router.get_best_route(token, base, amount)
            if not protos:
                return False
            info = await protos[0].get_liquidity_info(route[0], route[1], amount)
            if info.liquidity < amount * self.liquidity_threshold:
                self.logger.error("Insufficient liquidity for %s", token)
                return False
            return True
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Liquidity check failed: %s", exc)
            return False

    def check_concentration(self) -> bool:
        for token, item in self.inventory.items():
            if item.allocation > self.concentration_limit:
                self.logger.error("Concentration too high for %s", token)
                return False
        return True

    def stress_test(self, shock_pct: float) -> float:
        if shock_pct <= 0:
            raise InventoryError("shock_pct must be positive")
        loss = 0.0
        for item in self.inventory.values():
            loss += item.balance * item.price * shock_pct
        self.logger.info(
            "Stress test %.2f%% loss: %.4f", shock_pct * 100, loss
        )
        return loss

    def snapshot(self) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            time.time(),
            self.equity,
            copy.deepcopy(self.inventory),
            list(self.positions),
        )


__all__ = [
    "RiskManager",
    "Position",
    "InventoryItem",
    "PortfolioSnapshot",
    "PortfolioRiskManager",
]

