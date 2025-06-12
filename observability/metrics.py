from __future__ import annotations

from prometheus_client import Counter, Histogram

TRADE_COUNT = Counter('trade_count_total', 'Number of trades executed')
TRADE_SUCCESS = Counter('trade_success_total', 'Number of successful trades')
TRADE_PNL = Counter('trade_pnl_total', 'Total realized P&L')
API_LATENCY = Histogram('api_latency_seconds', 'Latency of API calls')

__all__ = ['TRADE_COUNT', 'TRADE_SUCCESS', 'TRADE_PNL', 'API_LATENCY']
