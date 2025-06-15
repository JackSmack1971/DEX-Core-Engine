import os
from unittest.mock import AsyncMock

import pytest

from models.trade_requests import EnhancedTradeRequest
from routing import Router


@pytest.mark.asyncio
async def test_router_execute_trade(monkeypatch):
    token_in = os.environ["TOKEN0_ADDRESS"]
    token_out = os.environ["TOKEN1_ADDRESS"]
    req = EnhancedTradeRequest(token_pair=(token_in, token_out), amount=1, price=1)
    router = Router([])
    monkeypatch.setattr(router, "execute_swap", AsyncMock(return_value="tx"))
    tx = await router.execute_trade(req)
    router.execute_swap.assert_awaited_once_with(1, token_in, token_out)
    assert tx == "tx"


def test_trade_request_validation():
    token = os.environ["TOKEN0_ADDRESS"]
    with pytest.raises(ValueError):
        EnhancedTradeRequest(token_pair=(token, token), amount=1, price=1)
