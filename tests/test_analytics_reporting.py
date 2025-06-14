import json
import csv

import pytest

from analytics.reporting import (
    _aggregate_returns,
    generate_report,
    export_json,
    export_csv,
    ReportingError,
)


def test_aggregate_returns_valid():
    returns = [1.0, -0.5, 0.2, 0.3]
    result = _aggregate_returns(returns, 2)
    assert result == [0.5, 0.5]


def test_aggregate_returns_invalid():
    with pytest.raises(ReportingError):
        _aggregate_returns([0.1], 0)


def test_generate_report():
    report = generate_report("daily", [0.1, -0.05, 0.2])
    assert report["period"] == "daily"
    assert "total_pnl" in report
    assert "average_pnl" in report
    assert "max_drawdown" in report


@pytest.mark.asyncio
async def test_export_json_csv(tmp_path):
    data = {"a": 1, "b": 2}
    jpath = tmp_path / "f.json"
    cpath = tmp_path / "f.csv"
    await export_json(data, str(jpath))
    await export_csv(data, str(cpath))
    with open(jpath, "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert saved == data
    with open(cpath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    assert rows[0] == list(data.keys())


@pytest.mark.asyncio
async def test_export_invalid_extension(tmp_path):
    data = {"x": 1}
    bad = tmp_path / "bad.txt"
    with pytest.raises(ReportingError):
        await export_json(data, str(bad))
    with pytest.raises(ReportingError):
        await export_csv(data, str(bad))
