from __future__ import annotations

from prometheus_client import Gauge

ANALYTICS_PNL = Gauge(
    "analytics_pnl",
    "Current cumulative profit and loss computed by the analytics engine",
)
ANALYTICS_DRAWDOWN = Gauge(
    "analytics_drawdown",
    "Current portfolio drawdown computed by the analytics engine",
)
ROLLING_PERFORMANCE_7D = Gauge(
    "rolling_performance_7d",
    "Seven-day rolling performance",
)
ROLLING_PERFORMANCE_30D = Gauge(
    "rolling_performance_30d",
    "Thirty-day rolling performance",
)

__all__ = [
    "ANALYTICS_PNL",
    "ANALYTICS_DRAWDOWN",
    "ROLLING_PERFORMANCE_7D",
    "ROLLING_PERFORMANCE_30D",
]
