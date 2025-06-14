from fastapi.testclient import TestClient

from api import app, risk_manager

client = TestClient(app)


def test_report_endpoint_valid():
    risk_manager.returns.clear()
    risk_manager.update_equity(0.1)
    risk_manager.update_equity(-0.05)
    resp = client.get("/analytics/report", params={"period": "daily"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_pnl"] != 0


def test_report_endpoint_invalid():
    resp = client.get("/analytics/report", params={"period": "yearly"})
    assert resp.status_code == 503


def test_performance_endpoint():
    risk_manager.returns.clear()
    for r in [0.1, -0.05, 0.2]:
        risk_manager.update_equity(r)
    resp = client.get("/analytics/performance", params={"confidence": 0.9})
    assert resp.status_code == 200
    data = resp.json()
    assert "var" in data and "sharpe" in data


def test_performance_invalid_confidence():
    resp = client.get("/analytics/performance", params={"confidence": 1.5})
    assert resp.status_code == 503

