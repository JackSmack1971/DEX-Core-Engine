import pytest

from analytics.visualization import (
    prepare_pl_curve,
    prepare_drawdown,
    prepare_dashboard_data,
)


def test_prepare_pl_curve_and_drawdown():
    returns = [1.0, -0.5, 0.2]
    curve = prepare_pl_curve(returns)
    assert curve == [1.0, 0.5, 0.7]
    dd = prepare_drawdown(returns)
    assert dd == pytest.approx([0.0, -0.5, -0.3])


def test_prepare_dashboard_data():
    returns = [0.1, 0.1, -0.2]
    data = prepare_dashboard_data(returns)
    assert data["pl_curve"] == prepare_pl_curve(returns)
    assert data["drawdown"] == prepare_drawdown(returns)
