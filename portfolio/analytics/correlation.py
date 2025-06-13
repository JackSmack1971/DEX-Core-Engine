from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async


class CorrelationEngine:
    """Compute pairwise return correlations."""

    def __init__(self) -> None:
        self._circuit = CircuitBreaker()

    async def compute(self, returns: Dict[str, List[float]]) -> Dict[Tuple[str, str], float]:
        async def _compute() -> Dict[Tuple[str, str], float]:
            result: Dict[Tuple[str, str], float] = {}
            symbols = list(returns)
            for i, a in enumerate(symbols):
                for b in symbols[i + 1 :]:
                    ra = returns[a]
                    rb = returns[b]
                    if not ra or not rb:
                        result[(a, b)] = 0.0
                        continue
                    mean_a = sum(ra) / len(ra)
                    mean_b = sum(rb) / len(rb)
                    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(ra, rb)) / len(ra)
                    var_a = sum((x - mean_a) ** 2 for x in ra) / len(ra)
                    var_b = sum((y - mean_b) ** 2 for y in rb) / len(rb)
                    denom = (var_a * var_b) ** 0.5
                    result[(a, b)] = cov / denom if denom else 0.0
            return result

        return await self._circuit.call(retry_async, _compute)


__all__ = ["CorrelationEngine"]
