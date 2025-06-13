import os
os.environ.setdefault("RPC_URL", "http://localhost")
os.environ.setdefault("PRIVATE_KEY", "key")
os.environ.setdefault("WALLET_ADDRESS", "0x0000000000000000000000000000000000000005")
os.environ.setdefault("TOKEN0_ADDRESS", "0x0000000000000000000000000000000000000001")
os.environ.setdefault("TOKEN1_ADDRESS", "0x0000000000000000000000000000000000000002")
os.environ.setdefault("UNISWAP_V2_ROUTER", "0x0000000000000000000000000000000000000003")
os.environ.setdefault("SUSHISWAP_ROUTER", "0x0000000000000000000000000000000000000004")

from unittest.mock import MagicMock
import asyncio

import pytest

from exceptions import DexError, StrategyError
from dex_handler import DEXHandler
from web3_service import TransactionFailedError
from routing import Router
from strategy import ArbitrageStrategy


def test_strategy_initializes_without_error():
    router = Router([])
    assert isinstance(ArbitrageStrategy(router), ArbitrageStrategy)


def test_execute_swap_raises_dex_error():
    handler = DEXHandler.__new__(DEXHandler)
    handler.web3_service = MagicMock()
    handler.contract = MagicMock()
    handler.web3_service.account = MagicMock(address="0xabc")
    handler.web3_service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    handler._circuit = MagicMock(call=lambda f, *a, **kw: f(*a, **kw))

    built_tx = {"tx": 1}
    swap_func = MagicMock(return_value=MagicMock(build_transaction=MagicMock(return_value=built_tx)))
    handler.contract.functions.swapExactETHForTokens = swap_func
    async def fail_tx(*args, **kwargs):
        raise TransactionFailedError("fail")

    handler.web3_service.sign_and_send_transaction.side_effect = fail_tx

    with pytest.raises(DexError):
        asyncio.run(handler.execute_swap(1, ["a", "b"]))

