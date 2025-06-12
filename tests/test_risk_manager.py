from risk_manager import RiskManager


def test_position_size_fixed_fractional():
    rm = RiskManager()
    size = rm.position_size(1000.0, 0.02)
    assert size <= 1000.0


def test_drawdown_trigger():
    rm = RiskManager()
    rm.update_equity(-0.3)
    assert rm.check_drawdown() is True


def test_stop_loss_close():
    rm = RiskManager()
    pos = rm.add_position(100.0, 1000.0, 0.02)
    closed = rm.monitor(90.0)
    assert pos in closed


def test_var_and_sharpe():
    rm = RiskManager()
    for i in range(10):
        rm.update_equity(0.1 if i % 2 else -0.05)
    assert rm.var() >= 0
    assert rm.sharpe() >= 0


def test_shutdown_clears_positions():
    rm = RiskManager()
    rm.add_position(100.0, 1000.0, 0.02)
    rm.shutdown()
    assert not rm.positions

