from __future__ import annotations

import os
from collections import defaultdict
from typing import Dict, List, Tuple

import httpx

from risk_manager import RiskManager
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async


class AnalyticsError(Exception):
    """Raised when analytics operations fail."""


class AnalyticsEngine:
    """Compute portfolio analytics and P&L metrics."""

    def __init__(self, risk_manager: RiskManager, base_currency: str = "USD") -> None:
        self.risk_manager = risk_manager
        self.base_currency = base_currency
        self.strategy_returns: Dict[str, List[float]] = defaultdict(list)
        self.strategy_assets: Dict[str, List[str]] = defaultdict(list)
        self._circuit = CircuitBreaker()

    async def _fetch_rate(self, src: str, dst: str) -> float:
        async def _get() -> float:
            url = os.environ.get("FX_API_URL")
            key = os.environ.get("FX_API_KEY")
            if not url or not key:
                raise AnalyticsError("missing FX API config")
            params = {"base": src, "symbols": dst, "api_key": key}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
            return float(data["rates"][dst])

        try:
            return await self._circuit.call(retry_async, _get)
        except Exception as exc:  # noqa: BLE001
            raise AnalyticsError(str(exc)) from exc

    async def _convert_price(self, price: float, src: str) -> float:
        if src == self.base_currency:
            return price
        rate = await self._fetch_rate(src, self.base_currency)
        return price * rate

    async def update_price(self, token: str, price: float, currency: str) -> None:
        if price <= 0 or not token:
            raise AnalyticsError("invalid parameters")
        conv = await self._convert_price(price, currency)
        self.risk_manager.set_price(token, conv)

    async def register_asset(
        self, strategy: str, token: str, amount: float, price: float, currency: str
    ) -> None:
        if amount <= 0 or price <= 0 or not strategy or not token:
            raise AnalyticsError("invalid parameters")
        conv = await self._convert_price(price, currency)
        self.risk_manager.add_inventory(token, amount)
        self.risk_manager.set_price(token, conv)
        item = self.risk_manager.inventory[token]
        item.metadata.setdefault("entry_price", conv)
        self.strategy_assets[strategy].append(token)

    def record_trade(self, strategy: str, pnl: float) -> None:
        self.strategy_returns[strategy].append(pnl)
        self.risk_manager.update_equity(pnl)

    def unrealized_pnl(self, token: str) -> float:
        item = self.risk_manager.inventory.get(token)
        if not item or "entry_price" not in item.metadata:
            return 0.0
        return (item.price - item.metadata["entry_price"]) * item.balance

    def pnl_per_strategy(self, strategy: str) -> Tuple[float, float]:
        realized = sum(self.strategy_returns.get(strategy, []))
        unreal = sum(self.unrealized_pnl(t) for t in self.strategy_assets.get(strategy, []))
        return realized, unreal

    def _ratio(self, returns: List[float], downside: bool = False) -> Tuple[float, float]:
        if not returns:
            return 0.0, 0.0
        avg = sum(returns) / len(returns)
        if downside:
            neg = [r for r in returns if r < 0]
            var = sum(r ** 2 for r in neg) / len(returns)
        else:
            var = sum((r - avg) ** 2 for r in returns) / len(returns)
        return avg, var ** 0.5

    def sortino_ratio(self, returns: List[float], risk_free: float = 0.0) -> float:
        avg, dd = self._ratio([r - risk_free for r in returns], downside=True)
        return 0.0 if dd == 0 else avg / dd

    def calmar_ratio(self, returns: List[float]) -> float:
        max_dd = self.max_drawdown(returns)
        avg = sum(returns) / len(returns) if returns else 0.0
        return 0.0 if max_dd == 0 else avg / abs(max_dd)

    def information_ratio(self, returns: List[float], benchmark: List[float]) -> float:
        diff = [a - b for a, b in zip(returns, benchmark)]
        avg, std = self._ratio(diff)
        return 0.0 if std == 0 else avg / std

    def win_rate(self, returns: List[float]) -> float:
        wins = [r for r in returns if r > 0]
        return len(wins) / len(returns) if returns else 0.0

    def average_win_loss(self, returns: List[float]) -> Tuple[float, float]:
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        return avg_win, avg_loss

    def profit_factor(self, returns: List[float]) -> float:
        gains = sum(r for r in returns if r > 0)
        loss = abs(sum(r for r in returns if r < 0))
        return gains / loss if loss else 0.0

    def rolling(self, returns: List[float], window: int) -> List[float]:
        if window <= 0:
            raise AnalyticsError("window must be positive")
        return [sum(returns[i : i + window]) / window for i in range(len(returns) - window + 1)]

    def max_drawdown(self, returns: List[float]) -> float:
        peak = drawdown = 0.0
        cum = 0.0
        for r in returns:
            cum += r
            peak = max(peak, cum)
            drawdown = min(drawdown, cum - peak)
        return drawdown

    def beta(self, returns: List[float], benchmark: List[float]) -> float:
        if not returns or not benchmark:
            return 0.0
        mean_r = sum(returns) / len(returns)
        mean_b = sum(benchmark) / len(benchmark)
        cov = sum((r - mean_r) * (b - mean_b) for r, b in zip(returns, benchmark)) / len(returns)
        var_b = sum((b - mean_b) ** 2 for b in benchmark) / len(benchmark)
        return cov / var_b if var_b else 0.0


__all__ = ["AnalyticsEngine", "AnalyticsError"]
