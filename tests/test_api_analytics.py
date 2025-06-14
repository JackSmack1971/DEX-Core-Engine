from fastapi.testclient import TestClient
from jose import jwt

from api import app, risk_manager
from api.auth import ALGORITHM, SECRET_KEY, UserRole


def _token(role: UserRole = UserRole.TRADER) -> str:
    payload = {"sub": "tester", "role": role.value}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

client = TestClient(app)


def test_report_endpoint_valid():
    risk_manager.returns.clear()
    risk_manager.update_equity(0.1)
    risk_manager.update_equity(-0.05)
    headers = {"Authorization": f"Bearer {_token()}"}
    resp = client.get("/analytics/report", params={"period": "daily"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_pnl"] != 0


def test_report_endpoint_invalid():
    headers = {"Authorization": f"Bearer {_token()}"}
    resp = client.get("/analytics/report", params={"period": "yearly"}, headers=headers)
    assert resp.status_code == 503


def test_performance_endpoint():
    risk_manager.returns.clear()
    for r in [0.1, -0.05, 0.2]:
        risk_manager.update_equity(r)
    headers = {"Authorization": f"Bearer {_token()}"}
    resp = client.get("/analytics/performance", params={"confidence": 0.9}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "var" in data and "sharpe" in data


def test_performance_invalid_confidence():
    headers = {"Authorization": f"Bearer {_token()}"}
    resp = client.get("/analytics/performance", params={"confidence": 1.5}, headers=headers)
    assert resp.status_code == 503


def test_unauthorized_access():
    resp = client.get("/analytics/report", params={"period": "daily"})
    assert resp.status_code == 401


def test_forbidden_role():
    headers = {"Authorization": f"Bearer {_token(UserRole.READ_ONLY)}"}
    resp = client.get("/metrics", headers=headers)
    assert resp.status_code == 403

