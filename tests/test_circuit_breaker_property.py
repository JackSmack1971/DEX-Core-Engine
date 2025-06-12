import asyncio
from hypothesis import given, strategies as st
import pytest

from utils.circuit_breaker import CircuitBreaker
from exceptions import ServiceUnavailableError


@given(st.integers(min_value=1, max_value=5))
@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures(threshold: int) -> None:
    cb = CircuitBreaker(failure_threshold=threshold, recovery_timeout=1)

    async def fail() -> None:
        raise ValueError("boom")

    for _ in range(threshold):
        with pytest.raises(ValueError):
            await cb.call(fail)
    assert cb._state == "open"
    with pytest.raises(ServiceUnavailableError):
        await cb.call(fail)
