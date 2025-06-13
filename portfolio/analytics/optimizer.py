from __future__ import annotations

from typing import Dict

from pulp import LpMaximize, LpProblem, LpVariable, lpSum

from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async


class OptimizationEngine:
    """Simple mean-variance optimizer."""

    def __init__(self) -> None:
        self._circuit = CircuitBreaker()

    async def optimize(self, returns: Dict[str, float], capital: float) -> Dict[str, float]:
        async def _opt() -> Dict[str, float]:
            symbols = list(returns)
            prob = LpProblem("portfolio", LpMaximize)
            weights = {s: LpVariable(s, lowBound=0) for s in symbols}
            prob += lpSum(returns[s] * weights[s] for s in symbols)
            prob += lpSum(weights[s] for s in symbols) == capital
            if prob.solve() != 1:
                raise RuntimeError("optimization failed")
            return {s: weights[s].value() or 0.0 for s in symbols}

        return await self._circuit.call(retry_async, _opt)


__all__ = ["OptimizationEngine"]
