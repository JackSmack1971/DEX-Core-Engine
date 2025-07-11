import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from dex_handler import DEXHandler
from slippage_protection import SlippageProtectionEngine
from exceptions import DexError
from tokens import detect


@pytest.mark.asyncio
async def test_balance_check_failure(monkeypatch):
    handler = DEXHandler.__new__(DEXHandler)
    handler.web3_service = MagicMock()
    handler.contract = MagicMock()
    handler.web3_service.account = MagicMock(address="0xabc")
    handler.web3_service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    handler._circuit = MagicMock(call=lambda f, *a, **kw: f(*a, **kw))

    handler.contract.functions.getAmountsOut = MagicMock(
        return_value=MagicMock(call=MagicMock(return_value=[1, 2]))
    )
    async def fake_thread(func, *a, **kw):
        return func()

    monkeypatch.setattr(asyncio, "to_thread", fake_thread)
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "calculate_protected_slippage",
        lambda amt: 1,
    )
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "validate_transaction_slippage",
        lambda *a, **kw: None,
    )

    swap_func = MagicMock(return_value=MagicMock(build_transaction=MagicMock(return_value={"tx": 1})))
    handler.contract.functions.swapExactETHForTokens = swap_func
    handler.web3_service.sign_and_send_transaction = AsyncMock(return_value={"transactionHash": b"\x01"})
    handler.web3_service.get_contract.return_value = MagicMock()

    monkeypatch.setattr(detect, "detect_token_type", AsyncMock(return_value=detect.TokenType.ERC20))
    monkeypatch.setattr(detect, "get_token_balance", AsyncMock(side_effect=[0, 0]))

    with pytest.raises(DexError):
        await handler.execute_swap(1, ["a", "b"])
