from __future__ import annotations

from typing import Dict, List


def attribute_returns(weights: Dict[str, float], returns: Dict[str, List[float]]) -> Dict[str, float]:
    """Compute contribution of each asset to portfolio return."""
    contrib: Dict[str, float] = {}
    periods = len(next(iter(returns.values()), []))
    if periods == 0:
        return {k: 0.0 for k in weights}
    for symbol, weight in weights.items():
        r = sum(returns.get(symbol, [0.0] * periods)) / periods
        contrib[symbol] = weight * r
    return contrib


__all__ = ["attribute_returns"]
