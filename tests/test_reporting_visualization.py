import json
import csv

import pytest

from analytics.reporting import (
    generate_report,
    export_json,
    export_csv,
    ReportingError,
)
from analytics.visualization import (
    prepare_pl_curve,
    prepare_drawdown,
    prepare_dashboard_data,
)


def test_prepare_visualization():
    returns = [1.0, -0.5, 0.2]
    curve = prepare_pl_curve(returns)
    assert curve == [1.0, 0.5, 0.7]
    dd = prepare_drawdown(returns)
    assert dd == pytest.approx([0.0, -0.5, -0.3])
    dash = prepare_dashboard_data(returns)
    assert dash["pl_curve"] == curve
    assert dash["drawdown"] == dd


@pytest.mark.asyncio
async def test_report_export(tmp_path, monkeypatch):
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))
    returns = [0.1] * 10
    report = generate_report("daily", returns)
    json_path = tmp_path / "r.json"
    csv_path = tmp_path / "r.csv"
    await export_json(report, str(json_path))
    await export_csv(report, str(csv_path))
    with open(json_path, "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert saved == report
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    assert rows[0] == list(report.keys())
    values = dict(zip(rows[0], rows[1]))
    assert float(values["average_pnl"]) == report["average_pnl"]


def test_generate_report_validation():
    with pytest.raises(ReportingError):
        generate_report("yearly", [1.0])

