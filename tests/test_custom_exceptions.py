import os
os.environ.setdefault("RPC_URL", "http://localhost")
os.environ.setdefault("PRIVATE_KEY", "key")
os.environ.setdefault("WALLET_ADDRESS", "addr")
os.environ.setdefault("TOKEN0_ADDRESS", "0x0000000000000000000000000000000000000001")
os.environ.setdefault("TOKEN1_ADDRESS", "0x0000000000000000000000000000000000000002")
os.environ.setdefault("UNISWAP_V2_ROUTER", "0x0000000000000000000000000000000000000003")
os.environ.setdefault("SUSHISWAP_ROUTER", "0x0000000000000000000000000000000000000004")

from unittest.mock import MagicMock

import pytest

from exceptions import DexError, StrategyError
from dex_handler import DEXHandler
from web3_service import TransactionFailedError
from strategy import ArbitrageStrategy


def test_strategy_error_raised():
    with pytest.raises(StrategyError):
        ArbitrageStrategy([MagicMock()])


def test_execute_swap_raises_dex_error():
    handler = DEXHandler.__new__(DEXHandler)
    handler.web3_service = MagicMock()
    handler.contract = MagicMock()
    handler.web3_service.account = MagicMock(address="0xabc")
    handler.web3_service.web3 = MagicMock(eth=MagicMock(gas_price=1))

    built_tx = {"tx": 1}
    swap_func = MagicMock(return_value=MagicMock(build_transaction=MagicMock(return_value=built_tx)))
    handler.contract.functions.swapExactETHForTokens = swap_func
    handler.web3_service.sign_and_send_transaction.side_effect = TransactionFailedError("fail")

    with pytest.raises(DexError):
        handler.execute_swap(1, ["a", "b"])

