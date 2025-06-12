"""Risk management utilities for trading."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Deque, List

import config
from exceptions import StrategyError
from logger import get_logger


logger = get_logger("risk_manager")


@dataclass
class Position:
    """Simple trade position."""

    entry_price: float
    size: float
    stop_loss: float
    take_profit: float


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


__all__ = ["RiskManager", "Position"]

