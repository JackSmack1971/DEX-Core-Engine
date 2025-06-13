from __future__ import annotations

"""Profit optimization utilities."""

from dataclasses import dataclass
from typing import List

import pulp

from exceptions import StrategyError
from observability.metrics import (
    OPTIMIZATION_FAILURES,
    OPTIMIZATION_RUNS,
    RISK_ADJUSTED_PROFIT,
)
from slippage_protection import calculate_dynamic_slippage


@dataclass
class Opportunity:
    """Represents a trading opportunity."""

    expected_profit: float
    risk: float
    gas_cost: float
    price_impact: float
    volatility: float


class ProfitOptimizer:
    """Linear programming based optimizer for capital allocation."""

    def __init__(self, max_capital: float) -> None:
        if max_capital <= 0:
            raise ValueError("max_capital must be positive")
        self.max_capital = max_capital

    def optimize(
        self,
        options: List[Opportunity],
        risk_weight: float = 1.0,
        gas_weight: float = 1.0,
    ) -> List[float]:
        """Return capital allocation for ``options``."""
        if not options:
            return []
        problem = pulp.LpProblem("profit_opt", pulp.LpMaximize)
        vars = [pulp.LpVariable(f"alloc_{i}", lowBound=0) for i in range(len(options))]
        problem += pulp.lpSum(vars) <= self.max_capital
        profits = []
        for opt in options:
            slip = calculate_dynamic_slippage(opt.price_impact, opt.volatility)
            profits.append(
                opt.expected_profit - risk_weight * opt.risk - gas_weight * opt.gas_cost - slip
            )
        problem += pulp.lpSum(v * p for v, p in zip(vars, profits))
        status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
        if status != pulp.LpStatusOptimal:
            OPTIMIZATION_FAILURES.inc()
            raise StrategyError("optimization failed")
        OPTIMIZATION_RUNS.inc()
        allocation = [float(v.varValue or 0.0) for v in vars]
        RISK_ADJUSTED_PROFIT.observe(sum(p * a for p, a in zip(profits, allocation)))
        return allocation


__all__ = ["ProfitOptimizer", "Opportunity"]
