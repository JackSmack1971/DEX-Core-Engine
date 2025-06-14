from __future__ import annotations

"""Abstract strategy classes and metrics."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from risk_manager import RiskManager
from routing import Router
from logger import get_logger
from observability.decorators import log_and_measure


@dataclass
class StrategyConfig:
    """Configuration for strategy-specific parameters."""

    name: str
    enabled: bool = True
    risk_params: Dict[str, Any] | None = None
    custom_params: Dict[str, Any] | None = None


@dataclass
class StrategyMetrics:
    """Performance metrics for strategy evaluation."""

    total_trades: int = 0
    successful_trades: int = 0
    total_pnl: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    rolling_returns: List[float] = field(default_factory=list)


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(
        self,
        router: Router,
        config: StrategyConfig,
        risk_manager: Optional[RiskManager] = None,
    ) -> None:
        self.router = router
        self.config = config
        self.risk_manager = risk_manager or RiskManager()
        self.logger = get_logger(f"strategy_{config.name}")
        self.metrics = StrategyMetrics()
        self.is_running = False
        self._setup_strategy()

    def _setup_strategy(self) -> None:
        """Hook for subclasses to initialize resources."""

    @abstractmethod
    async def analyze_market(self) -> Dict[str, Any]:
        """Analyze market conditions and return signals."""

    @abstractmethod
    async def generate_signals(
        self, market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate trading signals based on market analysis."""

    @abstractmethod
    async def execute_trades(self, signals: List[Dict[str, Any]]) -> List[str]:
        """Execute trades based on generated signals."""

    @log_and_measure("strategy", warn_ms=1000)
    async def run_cycle(self) -> None:
        """Execute one strategy cycle of analysis and trading."""
        market = await self.analyze_market()
        signals = await self.generate_signals(market)
        txs = await self.execute_trades(signals)
        if txs:
            self.metrics.total_trades += len(txs)
            self.metrics.successful_trades += len(txs)

    async def start(self) -> None:
        """Start the strategy execution loop."""
        self.is_running = True
        while self.is_running:
            try:
                await self.run_cycle()
            except Exception as exc:  # noqa: BLE001
                self.logger.exception("cycle failed: %s", exc)
            await asyncio.sleep(0)

    async def stop(self) -> None:
        """Stop the strategy execution."""
        self.is_running = False

    def get_metrics(self) -> StrategyMetrics:
        """Return current strategy performance metrics."""
        return self.metrics


__all__ = ["StrategyConfig", "StrategyMetrics", "BaseStrategy"]
