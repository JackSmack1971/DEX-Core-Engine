from analytics.metrics import (
    ANALYTICS_PNL,
    ANALYTICS_DRAWDOWN,
    ROLLING_PERFORMANCE_7D,
    ROLLING_PERFORMANCE_30D,
)


def test_analytics_metrics_gauges():
    ANALYTICS_PNL.set(10.0)
    ANALYTICS_DRAWDOWN.set(-2.0)
    ROLLING_PERFORMANCE_7D.set(0.05)
    ROLLING_PERFORMANCE_30D.set(0.2)
    assert ANALYTICS_PNL._value.get() == 10.0
    assert ANALYTICS_DRAWDOWN._value.get() == -2.0
    assert ROLLING_PERFORMANCE_7D._value.get() == 0.05
    assert ROLLING_PERFORMANCE_30D._value.get() == 0.2
