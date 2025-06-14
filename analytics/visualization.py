from __future__ import annotations

from typing import Dict, List


def prepare_pl_curve(returns: List[float]) -> List[float]:
    curve: List[float] = []
    total = 0.0
    for r in returns:
        total += r
        curve.append(total)
    return curve


def prepare_drawdown(returns: List[float]) -> List[float]:
    curve = prepare_pl_curve(returns)
    drawdown: List[float] = []
    peak = 0.0
    for val in curve:
        peak = max(peak, val)
        drawdown.append(val - peak)
    return drawdown


def prepare_dashboard_data(returns: List[float]) -> Dict[str, List[float]]:
    return {
        "pl_curve": prepare_pl_curve(returns),
        "drawdown": prepare_drawdown(returns),
    }

