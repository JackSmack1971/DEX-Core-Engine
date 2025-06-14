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
SLIPPAGE_APPLIED = Histogram(
    'slippage_applied_percent',
    'Slippage percentage applied to trades',
)
SLIPPAGE_VIOLATIONS = Counter(
    'slippage_violations_total',
    'Number of swaps exceeding slippage limits',
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

# Database metrics
DB_HEALTH_CHECKS = Counter(
    'db_health_checks_total',
    'Total number of database health checks',
)
DB_HEALTH_FAILURES = Counter(
    'db_health_failures_total',
    'Number of failed database health checks',
)
DB_ACTIVE_CONNECTIONS = Gauge(
    'db_active_connections',
    'Currently active database connections',
)
__all__ = [
    'TRADE_COUNT',
    'TRADE_SUCCESS',
    'TRADE_PNL',
    'API_LATENCY',
    'SLIPPAGE_CHECKS',
    'SLIPPAGE_REJECTED',
    'SLIPPAGE_APPLIED',
    'SLIPPAGE_VIOLATIONS',
    'OPTIMIZATION_RUNS',
    'OPTIMIZATION_FAILURES',
    'RISK_ADJUSTED_PROFIT',
    'PORTFOLIO_VALUE',
    'REBALANCE_COUNT',
    'DB_HEALTH_CHECKS',
    'DB_HEALTH_FAILURES',
    'DB_ACTIVE_CONNECTIONS',
]
