import asyncio
from unittest.mock import AsyncMock

import pytest

from models.trade_requests import EnhancedTradeRequest
from trading.async_validators import (
    AsyncFinancialTransactionValidator,
    ValidationError,
    RiskModelError,
)


@pytest.mark.asyncio
async def test_validate_request_pass(monkeypatch):
    validator = AsyncFinancialTransactionValidator()
    monkeypatch.setattr(validator, "score_risk", AsyncMock(return_value=0.1))
    req = EnhancedTradeRequest(token_pair=("0x0000000000000000000000000000000000000001", "0x0000000000000000000000000000000000000002"), amount=1.0, price=1.0)
    assert await validator.validate_request(req)


@pytest.mark.asyncio
async def test_validate_request_high_risk(monkeypatch):
    validator = AsyncFinancialTransactionValidator()
    monkeypatch.setattr(validator, "score_risk", AsyncMock(return_value=0.9))
    req = EnhancedTradeRequest(token_pair=("0x0000000000000000000000000000000000000001", "0x0000000000000000000000000000000000000002"), amount=1.0, price=1.0)
    with pytest.raises(ValidationError):
        await validator.validate_request(req)


@pytest.mark.asyncio
async def test_validate_request_timeout(monkeypatch):
    validator = AsyncFinancialTransactionValidator(timeout=0.05)

    async def slow_score(_: EnhancedTradeRequest) -> float:
        await asyncio.sleep(0.1)
        return 0.1

    monkeypatch.setattr(validator, "score_risk", slow_score)
    req = EnhancedTradeRequest(token_pair=("0x0000000000000000000000000000000000000001", "0x0000000000000000000000000000000000000002"), amount=1.0, price=1.0)
    with pytest.raises(RiskModelError):
        await validator.validate_request(req)


import os

class DummyResp:
    def __init__(self, score: float) -> None:
        self.score = score

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return {"risk_score": self.score}

class DummyClient:
    def __init__(self, score: float) -> None:
        self.score = score

    async def __aenter__(self) -> "DummyClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        pass

    async def post(self, *_: str, **__: object) -> DummyResp:
        return DummyResp(self.score)


@pytest.mark.asyncio
async def test_score_risk(monkeypatch):
    os.environ["RISK_MODEL_URL"] = "http://test"
    validator = AsyncFinancialTransactionValidator()
    monkeypatch.setattr("httpx.AsyncClient", lambda timeout: DummyClient(0.3))
    req = EnhancedTradeRequest(
        token_pair=(
            "0x0000000000000000000000000000000000000001",
            "0x0000000000000000000000000000000000000002",
        ),
        amount=1.0,
        price=1.0,
    )
    score = await validator.score_risk(req)
    assert score == 0.3

