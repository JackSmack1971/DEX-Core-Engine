from __future__ import annotations

"""Profit optimization utilities.

This module provides several linear programming optimizers that use
`pulp` to determine optimal capital allocations under different models.
Each optimizer records metrics on successful and failed optimization runs.
"""

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


class MarkowitzOptimizer(ProfitOptimizer):
    """Mean-variance optimizer using risk aversion."""

    def optimize(
        self, options: List[Opportunity], risk_aversion: float = 1.0
    ) -> List[float]:
        if not options:
            return []
        problem = pulp.LpProblem("markowitz_opt", pulp.LpMaximize)
        vars = [pulp.LpVariable(f"alloc_{i}", lowBound=0) for i in range(len(options))]
        problem += pulp.lpSum(vars) <= self.max_capital
        profits = []
        for opt in options:
            slip = calculate_dynamic_slippage(opt.price_impact, opt.volatility)
            profits.append(opt.expected_profit - risk_aversion * opt.risk - slip)
        problem += pulp.lpSum(v * p for v, p in zip(vars, profits))
        status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
        if status != pulp.LpStatusOptimal:
            OPTIMIZATION_FAILURES.inc()
            raise StrategyError("optimization failed")
        OPTIMIZATION_RUNS.inc()
        allocation = [float(v.varValue or 0.0) for v in vars]
        RISK_ADJUSTED_PROFIT.observe(sum(p * a for p, a in zip(profits, allocation)))
        return allocation


class BlackLittermanOptimizer(ProfitOptimizer):
    """Optimizer blending expected return with risk views."""

    def optimize(
        self,
        options: List[Opportunity],
        view_weight: float = 0.5,
        gas_weight: float = 1.0,
    ) -> List[float]:
        if not options:
            return []
        problem = pulp.LpProblem("black_litterman_opt", pulp.LpMaximize)
        vars = [pulp.LpVariable(f"alloc_{i}", lowBound=0) for i in range(len(options))]
        problem += pulp.lpSum(vars) <= self.max_capital
        profits = []
        for opt in options:
            slip = calculate_dynamic_slippage(opt.price_impact, opt.volatility)
            view = opt.expected_profit - (1 - view_weight) * opt.risk
            profits.append(view - gas_weight * opt.gas_cost - slip)
        problem += pulp.lpSum(v * p for v, p in zip(vars, profits))
        status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
        if status != pulp.LpStatusOptimal:
            OPTIMIZATION_FAILURES.inc()
            raise StrategyError("optimization failed")
        OPTIMIZATION_RUNS.inc()
        allocation = [float(v.varValue or 0.0) for v in vars]
        RISK_ADJUSTED_PROFIT.observe(sum(p * a for p, a in zip(profits, allocation)))
        return allocation


class RiskParityOptimizer(ProfitOptimizer):
    """Allocate capital to achieve equal weights."""

    def optimize(self, options: List[Opportunity]) -> List[float]:
        if not options:
            return []
        problem = pulp.LpProblem("risk_parity_opt", pulp.LpMinimize)
        vars = [pulp.LpVariable(f"alloc_{i}", lowBound=0) for i in range(len(options))]
        problem += pulp.lpSum(vars) == self.max_capital
        target = self.max_capital / len(options)
        devs = [pulp.LpVariable(f"dev_{i}", lowBound=0) for i in range(len(options))]
        for v, d in zip(vars, devs):
            problem += v - target <= d
            problem += target - v <= d
        problem += pulp.lpSum(devs)
        status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
        if status != pulp.LpStatusOptimal:
            OPTIMIZATION_FAILURES.inc()
            raise StrategyError("optimization failed")
        OPTIMIZATION_RUNS.inc()
        allocation = [float(v.varValue or 0.0) for v in vars]
        RISK_ADJUSTED_PROFIT.observe(-float(problem.objective.value()))
        return allocation


class FactorModelOptimizer(ProfitOptimizer):
    """Optimizer with factor exposure constraint."""

    def optimize(
        self,
        options: List[Opportunity],
        exposures: List[float],
        exposure_limit: float,
        risk_weight: float = 1.0,
        gas_weight: float = 1.0,
    ) -> List[float]:
        if not options:
            return []
        if len(exposures) != len(options):
            raise ValueError("exposures length mismatch")
        problem = pulp.LpProblem("factor_model_opt", pulp.LpMaximize)
        vars = [pulp.LpVariable(f"alloc_{i}", lowBound=0) for i in range(len(options))]
        problem += pulp.lpSum(vars) <= self.max_capital
        problem += pulp.lpSum(v * e for v, e in zip(vars, exposures)) <= exposure_limit
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


__all__ = [
    "ProfitOptimizer",
    "Opportunity",
    "MarkowitzOptimizer",
    "BlackLittermanOptimizer",
    "RiskParityOptimizer",
    "FactorModelOptimizer",
]
