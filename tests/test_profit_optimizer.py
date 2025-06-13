from optimization import ProfitOptimizer


def test_profit_optimizer_allocation():
    opt = ProfitOptimizer(max_capital=100)
    alloc = opt.optimize([1.0, 2.0, 0.5])
    assert alloc == [0.0, 100, 0.0]
