from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from exceptions import PriceManipulationError, ServiceUnavailableError
from logger import get_logger
from observability.metrics import SLIPPAGE_CHECKS, SLIPPAGE_REJECTED
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async
import config

logger = get_logger("slippage_protection")

# Minimum allowed slippage tolerance in percent
MIN_TOLERANCE_PERCENT = 0.1

# Message for disallowed zero-slippage transactions
ZERO_SLIPPAGE_MSG = "Zero slippage transactions are not allowed"


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
        if params.tolerance_percent < MIN_TOLERANCE_PERCENT:
            logger.info(
                "Tolerance %.2f%% below minimum %.2f%%, overriding",
                params.tolerance_percent,
                MIN_TOLERANCE_PERCENT,
            )
            params.tolerance_percent = MIN_TOLERANCE_PERCENT
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

    @staticmethod
    def calculate_protected_slippage(expected_amount: int) -> int:
        """Return minimum output amount respecting ``MAX_SLIPPAGE_BPS``."""
        if expected_amount <= 0:
            raise ValueError("expected_amount must be positive")
        bps = config.MAX_SLIPPAGE_BPS
        min_amount = int(expected_amount * (10000 - bps) / 10000)
        result = max(1, min_amount)
        logger.debug(
            "Calculated protected slippage: expected=%d bps=%d result=%d",
            expected_amount,
            bps,
            result,
        )
        return result

    @staticmethod
    def validate_transaction_slippage(expected_amount: int, actual_amount: int) -> None:
        """Validate that slippage between ``expected_amount`` and ``actual_amount``
        does not exceed ``MAX_SLIPPAGE_BPS``."""
        if expected_amount <= 0 or actual_amount < 0:
            raise ValueError("invalid amounts")
        diff_bps = abs(expected_amount - actual_amount) * 10000 / expected_amount
        logger.debug(
            "Validating tx slippage: expected=%d actual=%d diff=%.2f bps",
            expected_amount,
            actual_amount,
            diff_bps,
        )
        if diff_bps == 0:
            raise PriceManipulationError(ZERO_SLIPPAGE_MSG)
        if diff_bps > config.MAX_SLIPPAGE_BPS:
            raise PriceManipulationError(
                f"Slippage {diff_bps:.2f}bps exceeds max {config.MAX_SLIPPAGE_BPS}"
            )


def calculate_dynamic_slippage(price_impact: float, volatility: float) -> float:
    """Compute slippage adjusted for market volatility."""
    return price_impact * (1 + volatility)


__all__ = [
    "MarketConditions",
    "SlippageParams",
    "SlippageProtectionEngine",
    "MIN_TOLERANCE_PERCENT",
    "ZERO_SLIPPAGE_MSG",
    "calculate_dynamic_slippage",
    "calculate_protected_slippage",
    "validate_transaction_slippage",
    "analyze_market_conditions",
]
