from __future__ import annotations

"""Profit optimization utilities."""

from typing import List


class ProfitOptimizer:
    """Naive linear optimization for position sizing."""

    def __init__(self, max_capital: float) -> None:
        if max_capital <= 0:
            raise ValueError("max_capital must be positive")
        self.max_capital = max_capital

    def optimize(self, expected_profits: List[float]) -> List[float]:
        """Allocate capital to the most profitable opportunity."""
        if not expected_profits:
            return []
        idx = max(range(len(expected_profits)), key=lambda i: expected_profits[i])
        allocation = [0.0 for _ in expected_profits]
        allocation[idx] = self.max_capital
        return allocation


__all__ = ["ProfitOptimizer"]
