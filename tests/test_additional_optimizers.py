import pytest

from optimization import (
    Opportunity,
    MarkowitzOptimizer,
    BlackLittermanOptimizer,
    RiskParityOptimizer,
    FactorModelOptimizer,
)
from observability.metrics import OPTIMIZATION_FAILURES, OPTIMIZATION_RUNS


def patch_slippage(monkeypatch):
    monkeypatch.setattr(
        "optimization.calculate_dynamic_slippage",
        lambda impact, vol: impact * vol * 2,
    )


def example_options():
    return [
        Opportunity(5.0, 1.0, 0.5, 0.1, 0.2),
        Opportunity(4.0, 0.2, 0.1, 0.05, 0.1),
    ]


def test_markowitz_optimizer(monkeypatch):
    patch_slippage(monkeypatch)
    opt = MarkowitzOptimizer(max_capital=100)
    alloc = opt.optimize(example_options())
    assert alloc == [100.0, 0.0]


def test_black_litterman_optimizer(monkeypatch):
    patch_slippage(monkeypatch)
    opt = BlackLittermanOptimizer(max_capital=100)
    alloc = opt.optimize(example_options())
    assert alloc == [100.0, 0.0]


def test_risk_parity_optimizer(monkeypatch):
    patch_slippage(monkeypatch)
    opt = RiskParityOptimizer(max_capital=100)
    alloc = opt.optimize(example_options())
    assert alloc == [50.0, 50.0]


def test_factor_model_optimizer(monkeypatch):
    patch_slippage(monkeypatch)
    opt = FactorModelOptimizer(max_capital=100)
    alloc = opt.optimize(example_options(), exposures=[0.5, 0.1], exposure_limit=20)
    assert alloc == [0.0, 100.0]


@pytest.mark.parametrize(
    "optimizer_cls,args",
    [
        (MarkowitzOptimizer, {}),
        (BlackLittermanOptimizer, {}),
        (RiskParityOptimizer, {}),
        (FactorModelOptimizer, {"exposures": [0.1], "exposure_limit": 1}),
    ],
)
def test_optimizers_fail(monkeypatch, optimizer_cls, args):
    monkeypatch.setattr("optimization.pulp.LpProblem.solve", lambda self, *a, **kw: -1)
    opt = optimizer_cls(max_capital=10)
    start_fail = OPTIMIZATION_FAILURES._value.get()
    with pytest.raises(Exception):
        options = [Opportunity(1.0, 1.0, 1.0, 0.1, 0.1)]
        if optimizer_cls is FactorModelOptimizer:
            opt.optimize(options, **args)
        else:
            opt.optimize(options)
    assert OPTIMIZATION_FAILURES._value.get() == start_fail + 1
