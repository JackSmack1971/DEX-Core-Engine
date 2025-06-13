from __future__ import annotations

from typing import List

from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async


class RiskMetricsEngine:
    """Calculate risk measures like VaR."""

    def __init__(self) -> None:
        self._circuit = CircuitBreaker()

    async def var(self, returns: List[float], confidence: float = 0.95) -> float:
        async def _var() -> float:
            if not returns:
                return 0.0
            sorted_r = sorted(returns)
            idx = max(0, int((1 - confidence) * len(sorted_r)) - 1)
            return abs(sorted_r[idx])

        return await self._circuit.call(retry_async, _var)


__all__ = ["RiskMetricsEngine"]
