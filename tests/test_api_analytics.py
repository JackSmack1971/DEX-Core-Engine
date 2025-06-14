from fastapi.testclient import TestClient

from api import app
from analytics.metrics import (
    ANALYTICS_PNL,
    ANALYTICS_DRAWDOWN,
    ROLLING_PERFORMANCE_7D,
    ROLLING_PERFORMANCE_30D,
)


client = TestClient(app)


def test_analytics_performance_endpoint():
    ANALYTICS_PNL.set(10.0)
    ANALYTICS_DRAWDOWN.set(-1.0)
    ROLLING_PERFORMANCE_7D.set(0.1)
    ROLLING_PERFORMANCE_30D.set(0.2)
    response = client.get("/analytics/performance")
    assert response.status_code == 200
    data = response.json()
    assert data["pnl"] == 10.0
    assert data["drawdown"] == -1.0
    assert data["rolling_7d"] == 0.1
    assert data["rolling_30d"] == 0.2


def test_analytics_report_endpoint():
    payload = {"period": "daily", "returns": [1.0, -0.5, 0.2]}
    response = client.post("/analytics/report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "daily"
    assert "total_pnl" in data


def test_analytics_report_validation():
    payload = {"period": "yearly", "returns": [1.0]}
    response = client.post("/analytics/report", json=payload)
    assert response.status_code == 503
    data = response.json()
    assert data["error"] == "analytics_error"
