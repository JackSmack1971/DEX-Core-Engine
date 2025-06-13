from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge

TRADE_COUNT = Counter('trade_count_total', 'Number of trades executed')
TRADE_SUCCESS = Counter('trade_success_total', 'Number of successful trades')
TRADE_PNL = Counter('trade_pnl_total', 'Total realized P&L')
API_LATENCY = Histogram('api_latency_seconds', 'Latency of API calls')
SLIPPAGE_CHECKS = Counter('slippage_checks_total', 'Number of slippage checks')
SLIPPAGE_REJECTED = Counter(
    'slippage_rejected_total', 'Trades rejected due to slippage'
)
OPTIMIZATION_RUNS = Counter(
    'optimization_runs_total',
    'Number of profit optimization executions',
)
OPTIMIZATION_FAILURES = Counter(
    'optimization_failures_total',
    'Number of failed profit optimization attempts',
)
RISK_ADJUSTED_PROFIT = Histogram(
    'risk_adjusted_profit',
    'Risk-adjusted profit from optimizer',
)
PORTFOLIO_VALUE = Gauge('portfolio_value', 'Total portfolio value')
REBALANCE_COUNT = Counter('portfolio_rebalance_total', 'Number of portfolio rebalances')
__all__ = [
    'TRADE_COUNT',
    'TRADE_SUCCESS',
    'TRADE_PNL',
    'API_LATENCY',
    'SLIPPAGE_CHECKS',
    'SLIPPAGE_REJECTED',
    'OPTIMIZATION_RUNS',
    'OPTIMIZATION_FAILURES',
    'RISK_ADJUSTED_PROFIT',
    'PORTFOLIO_VALUE',
    'REBALANCE_COUNT',
]
