"""Arbitrage strategy built on the strategy framework."""

from __future__ import annotations

from typing import Any, Dict, List

import config
from routing import Router
from risk_manager import RiskManager
from strategies.base import BaseStrategy, StrategyConfig


class ArbitrageStrategy(BaseStrategy):
    """Simple arbitrage strategy between two DEXs."""

    def __init__(
        self,
        router: Router,
        strategy_config: StrategyConfig | None = None,
        risk_manager: RiskManager | None = None,
    ) -> None:
        cfg = strategy_config or StrategyConfig(name="arbitrage")
        super().__init__(router, cfg, risk_manager)
        self.token0 = config.TOKEN0_ADDRESS
        self.token1 = config.TOKEN1_ADDRESS

    def _check_profitability(self, start: float, end: float) -> List[Dict[str, Any]]:
        profit_margin = end - start
        self.logger.info(
            "Cycle start %.6f end %.6f profit %.6f",
            start,
            end,
            profit_margin,
        )
        if profit_margin > config.PROFIT_THRESHOLD:
            self.logger.info("Profitable opportunity found! Margin: %.6f", profit_margin)
            size = self.risk_manager.position_size(start, profit_margin)
            self.logger.info("Risk-approved size: %.4f", size)
            return [{"size": size}]
        self.logger.info("No profitable opportunity found. Standing by.")
        return []

    async def analyze_market(self) -> Dict[str, Any]:
        start_amount = 1.0
        token1_amt = await self.router.get_best_quote(self.token0, self.token1, start_amount)
        end_amount = await self.router.get_best_quote(self.token1, self.token0, token1_amt)
        return {"start": start_amount, "end": end_amount}

    async def generate_signals(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._check_profitability(market_data["start"], market_data["end"])

    async def execute_trades(self, signals: List[Dict[str, Any]]) -> List[str]:
        txs: List[str] = []
        for _ in signals:
            self.logger.warning("--- EXECUTION LOGIC DISABLED IN THIS EXAMPLE ---")
            txs.append("0x0")
        return txs

    async def run(self) -> None:
        """Backward compatible run loop."""
        await self.start()
