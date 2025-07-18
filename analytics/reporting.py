"""Functions for generating aggregated reports and exporting results."""
from __future__ import annotations

import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from logger import get_logger
from .visualization import prepare_pl_curve, prepare_drawdown


logger = get_logger("reporting")

def _allowed_export_dir() -> Path:
    """Return the base directory for allowed exports."""
    return Path(os.getenv("EXPORT_DIR", "exports")).resolve()


class ReportingError(Exception):
    """Raised when report generation or export fails."""


def _validate_export_path(path: str) -> Path:
    """Validate that ``path`` resides in the allowed export directory."""
    candidate = Path(path)
    if ".." in candidate.parts:
        raise ReportingError("path traversal detected")
    resolved = candidate.resolve()
    allowed = _allowed_export_dir()
    if not str(resolved).startswith(str(allowed)):
        raise ReportingError("path outside allowed directory")
    return resolved


def _aggregate_returns(returns: List[float], window: int) -> List[float]:
    if window <= 0:
        raise ReportingError("window must be positive")
    result: List[float] = []
    for i in range(0, len(returns), window):
        result.append(sum(returns[i : i + window]))
    return result


def generate_report(period: str, returns: List[float]) -> Dict[str, float]:
    if period not in {"daily", "weekly", "monthly"}:
        raise ReportingError("unsupported period")
    if not all(isinstance(r, (int, float)) for r in returns):
        raise ReportingError("invalid returns")
    window = {"daily": 1, "weekly": 7, "monthly": 30}[period]
    aggregated = _aggregate_returns(returns, window)
    pl_curve = prepare_pl_curve(aggregated)
    drawdown = prepare_drawdown(aggregated)
    report = {
        "period": period,
        "total_pnl": sum(aggregated),
        "average_pnl": sum(aggregated) / len(aggregated) if aggregated else 0.0,
        "max_drawdown": min(drawdown) if drawdown else 0.0,
    }
    logger.info("generated report", extra={"metadata": report})
    return report


async def export_json(data: Dict[str, Any], path: str) -> None:
    if not path.lower().endswith(".json"):
        raise ReportingError("path must end with .json")
    try:
        valid = _validate_export_path(path)
        await asyncio.to_thread(_write_json, valid, data)
        logger.info("exported json", extra={"metadata": {"path": str(valid)}})
    except Exception as exc:  # noqa: BLE001
        logger.error("json export failed: %s", exc)
        raise ReportingError(str(exc)) from exc


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


async def export_csv(data: Dict[str, Any], path: str) -> None:
    if not path.lower().endswith(".csv"):
        raise ReportingError("path must end with .csv")
    try:
        valid = _validate_export_path(path)
        await asyncio.to_thread(_write_csv, valid, data)
        logger.info("exported csv", extra={"metadata": {"path": str(valid)}})
    except Exception as exc:  # noqa: BLE001
        logger.error("csv export failed: %s", exc)
        raise ReportingError(str(exc)) from exc


def _write_csv(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(data.keys())
        writer.writerow([data[k] for k in data.keys()])

