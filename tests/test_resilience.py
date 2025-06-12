import asyncio
import time
from fastapi.testclient import TestClient
import pytest

from api import app
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async
from exceptions import ServiceUnavailableError


async def _fail_once(state: dict) -> int:
    if state.setdefault("count", 0) < 1:
        state["count"] += 1
        raise ValueError("fail")
    return 42


def test_retry_async():
    state = {}
    result = asyncio.run(retry_async(_fail_once, state, retries=3, base_delay=0.01))
    assert result == 42


def test_circuit_breaker_trips():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    async def fail():
        raise ValueError()

    for _ in range(2):
        with pytest.raises(ValueError):
            asyncio.run(cb.call(fail))
    with pytest.raises(ServiceUnavailableError):
        asyncio.run(cb.call(fail))
    time.sleep(0.11)
    with pytest.raises(ValueError):
        asyncio.run(cb.call(fail))


def test_rate_limit_and_health_endpoints():
    client = TestClient(app)
    for _ in range(100):
        r = client.get("/health")
        assert r.status_code == 200
    r = client.get("/health")
    assert r.status_code == 429
    r = client.get("/ready")
    assert r.status_code == 429
