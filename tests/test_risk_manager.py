from risk_manager import RiskManager
import pytest


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


def test_update_equity_updates_metrics():
    rm = RiskManager()
    rm.update_equity(0.1)
    from analytics.metrics import (
        ANALYTICS_PNL,
        ROLLING_PERFORMANCE_7D,
        ROLLING_PERFORMANCE_30D,
    )

    for _ in range(6):
        rm.update_equity(0.1)
    for _ in range(23):
        rm.update_equity(0.1)
    assert ANALYTICS_PNL._value.get() == pytest.approx(3.0)
    assert ROLLING_PERFORMANCE_7D._value.get() == pytest.approx(0.1)
    assert ROLLING_PERFORMANCE_30D._value.get() == pytest.approx(0.1)


def test_check_drawdown_sets_metric():
    rm = RiskManager()
    rm.update_equity(-0.2)
    from analytics.metrics import ANALYTICS_DRAWDOWN

    rm.check_drawdown()
    dd = 1 - rm.equity / rm.high_water
    assert ANALYTICS_DRAWDOWN._value.get() == pytest.approx(-dd)

