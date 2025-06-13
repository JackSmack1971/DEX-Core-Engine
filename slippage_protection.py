from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from exceptions import PriceManipulationError, ServiceUnavailableError
from logger import get_logger
from observability.metrics import SLIPPAGE_CHECKS, SLIPPAGE_REJECTED
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async

logger = get_logger("slippage_protection")


@dataclass
class MarketConditions:
    """Current market data for slippage checks."""

    price: float
    liquidity: float
    volatility: float


@dataclass
class SlippageParams:
    """Parameters controlling slippage protection."""

    tolerance_percent: float
    data_api: Optional[str] = None


class SlippageProtectionEngine:
    """Check slippage tolerance using external market data."""

    def __init__(self, params: SlippageParams) -> None:
        self.params = params
        self._circuit = CircuitBreaker()

    async def _fetch_market_data(self) -> MarketConditions:
        if not self.params.data_api:
            raise ServiceUnavailableError("market data endpoint not configured")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self.params.data_api)
            response.raise_for_status()
            data = response.json()
        return MarketConditions(
            price=float(data["price"]),
            liquidity=float(data.get("liquidity", 0)),
            volatility=float(data.get("volatility", 0)),
        )

    async def get_market_conditions(self) -> MarketConditions:
        try:
            return await self._circuit.call(retry_async, self._fetch_market_data)
        except Exception as exc:  # noqa: BLE001
            logger.error("Market data fetch failed: %s", exc)
            raise

    def analyze_market_conditions(self, market: MarketConditions) -> str:
        """Classify market environment."""
        if market.volatility > 0.5:
            return "volatile"
        if market.liquidity < 10:
            return "illiquid"
        return "stable"

    async def check(self, expected_price: float, amount: float) -> None:
        if expected_price <= 0 or amount < 0:
            raise ValueError("invalid expected_price or amount")
        SLIPPAGE_CHECKS.inc()
        market = await self.get_market_conditions()
        slippage = abs(market.price - expected_price) / expected_price * 100
        if slippage > self.params.tolerance_percent:
            SLIPPAGE_REJECTED.inc()
            raise PriceManipulationError(f"Slippage {slippage:.2f}% exceeds tolerance")
        if amount > market.liquidity:
            logger.warning(
                "Trade amount %.4f exceeds liquidity %.4f",
                amount,
                market.liquidity,
            )
        logger.info(
            "Slippage %.2f%% within tolerance %.2f%%",
            slippage,
            self.params.tolerance_percent,
        )


def calculate_dynamic_slippage(price_impact: float, volatility: float) -> float:
    """Compute slippage adjusted for market volatility."""
    return price_impact * (1 + volatility)


__all__ = [
    "MarketConditions",
    "SlippageParams",
    "SlippageProtectionEngine",
    "calculate_dynamic_slippage",
    "analyze_market_conditions",
]
