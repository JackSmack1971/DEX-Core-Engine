import pytest

from optimization import Opportunity, ProfitOptimizer
from observability.metrics import OPTIMIZATION_FAILURES, OPTIMIZATION_RUNS


def test_profit_optimizer_allocation(monkeypatch):
    monkeypatch.setattr(
        'optimization.calculate_dynamic_slippage',
        lambda impact, vol: impact * vol * 2,
    )
    opts = [
        Opportunity(5.0, 1.0, 0.5, 0.1, 0.2),
        Opportunity(4.0, 0.2, 0.1, 0.05, 0.1),
    ]
    opt = ProfitOptimizer(max_capital=100)
    start = OPTIMIZATION_RUNS._value.get()
    alloc = opt.optimize(opts)
    assert alloc == [0.0, 100.0]
    assert OPTIMIZATION_RUNS._value.get() == start + 1


def test_optimizer_metrics(monkeypatch):
    monkeypatch.setattr(
        'optimization.pulp.LpProblem.solve',
        lambda self, *a, **kw: -1,
    )
    opt = ProfitOptimizer(max_capital=10)
    start_fail = OPTIMIZATION_FAILURES._value.get()
    with pytest.raises(Exception):
        opt.optimize([Opportunity(1.0, 1.0, 1.0, 0.1, 0.1)])
    assert OPTIMIZATION_FAILURES._value.get() == start_fail + 1
