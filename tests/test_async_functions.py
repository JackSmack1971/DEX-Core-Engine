import os
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

os.environ.setdefault("RPC_URL", "http://localhost")
os.environ.setdefault("ENCRYPTED_PRIVATE_KEY", "encrypted")
os.environ.setdefault("WALLET_ADDRESS", "0x0000000000000000000000000000000000000005")
os.environ.setdefault("TOKEN0_ADDRESS", "0x0000000000000000000000000000000000000001")
os.environ.setdefault("TOKEN1_ADDRESS", "0x0000000000000000000000000000000000000002")
os.environ.setdefault("UNISWAP_V2_ROUTER", "0x0000000000000000000000000000000000000003")
os.environ.setdefault("SUSHISWAP_ROUTER", "0x0000000000000000000000000000000000000004")

from dex_handler import DEXHandler
from slippage_protection import SlippageProtectionEngine
from exceptions import DexError, PriceManipulationError
from strategy import ArbitrageStrategy
from observability.metrics import (
    TRADE_COUNT,
    TRADE_SUCCESS,
    SLIPPAGE_APPLIED,
    SLIPPAGE_VIOLATIONS,
)


@pytest.mark.asyncio
async def test_get_price_success(monkeypatch):
    handler = DEXHandler.__new__(DEXHandler)
    handler.contract = MagicMock()
    handler._circuit = MagicMock(call=lambda f, *a, **kw: f(*a, **kw))

    call_mock = MagicMock(return_value=[10**18, 2 * 10**18])
    func_mock = MagicMock(return_value=MagicMock(call=call_mock))
    handler.contract.functions.getAmountsOut = func_mock

    async def fake_to_thread(func, *args, **kwargs):
        return func()

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    price = await handler.get_price("a", "b")
    assert price == 2.0


@pytest.mark.asyncio
async def test_get_price_error(monkeypatch):
    handler = DEXHandler.__new__(DEXHandler)
    handler.contract = MagicMock()
    handler._circuit = MagicMock(call=lambda f, *a, **kw: f(*a, **kw))

    call_mock = MagicMock(side_effect=ValueError("fail"))
    func_mock = MagicMock(return_value=MagicMock(call=call_mock))
    handler.contract.functions.getAmountsOut = func_mock

    async def fake_to_thread(func, *args, **kwargs):
        return func()

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    price = await handler.get_price("a", "b")
    assert price == 0.0


@pytest.mark.asyncio
async def test_arbitrage_run_once(monkeypatch):
    router = MagicMock()
    router.get_best_quote = AsyncMock(side_effect=[1.0, 2.0])

    strategy = ArbitrageStrategy(router)
    strategy._check_profitability = MagicMock()

    async def stop_sleep(_):
        raise asyncio.CancelledError()

    monkeypatch.setattr(asyncio, "sleep", stop_sleep)

    with pytest.raises(asyncio.CancelledError):
        await strategy.run()

    strategy._check_profitability.assert_called_with(1.0, 2.0)

@pytest.mark.asyncio
async def test_execute_swap_increments_metrics(monkeypatch):
    handler = DEXHandler.__new__(DEXHandler)
    handler.web3_service = MagicMock()
    handler.contract = MagicMock()
    handler.web3_service.account = MagicMock(address="0xabc")
    handler.web3_service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    handler._circuit = MagicMock(call=lambda f, *a, **kw: f(*a, **kw))
    handler._do_swap = AsyncMock(return_value="0xdead")
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
    start_count = TRADE_COUNT._value.get()
    start_success = TRADE_SUCCESS._value.get()
    start_sum = SLIPPAGE_APPLIED._sum.get()
    tx_hash = await handler.execute_swap(1, ["a", "b"])
    assert tx_hash == "0xdead"
    assert TRADE_COUNT._value.get() == start_count + 1
    assert TRADE_SUCCESS._value.get() == start_success + 1
    assert SLIPPAGE_APPLIED._sum.get() > start_sum


@pytest.mark.asyncio
async def test_execute_swap_slippage_violation(monkeypatch):
    handler = DEXHandler.__new__(DEXHandler)
    handler.web3_service = MagicMock()
    handler.contract = MagicMock()
    handler.web3_service.account = MagicMock(address="0xabc")
    handler.web3_service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    handler._circuit = MagicMock(call=lambda f, *a, **kw: f(*a, **kw))
    handler._do_swap = AsyncMock(return_value="0xdead")
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
        lambda *a, **kw: (_ for _ in ()).throw(PriceManipulationError("bad")),
    )

    start_violations = SLIPPAGE_VIOLATIONS._value.get()
    with pytest.raises(DexError):
        await handler.execute_swap(1, ["a", "b"])
    assert SLIPPAGE_VIOLATIONS._value.get() == start_violations + 1


@pytest.mark.asyncio
async def test_execute_swap_zero_slippage_rejected(monkeypatch):
    handler = DEXHandler.__new__(DEXHandler)
    handler.web3_service = MagicMock()
    handler.contract = MagicMock()
    handler.web3_service.account = MagicMock(address="0xabc")
    handler.web3_service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    handler._circuit = MagicMock(call=lambda f, *a, **kw: f(*a, **kw))
    handler._do_swap = AsyncMock(return_value="0xdead")
    handler.contract.functions.getAmountsOut = MagicMock(
        return_value=MagicMock(call=MagicMock(return_value=[1, 2]))
    )

    async def fake_thread(func, *a, **kw):
        return func()

    monkeypatch.setattr(asyncio, "to_thread", fake_thread)
    monkeypatch.setattr(
        SlippageProtectionEngine,
        "calculate_protected_slippage",
        lambda amt: amt,
    )
    called = {"count": 0}
    orig_validate = SlippageProtectionEngine.validate_transaction_slippage

    def _validate(expected: int, actual: int) -> None:
        called["count"] += 1
        orig_validate(expected, actual)

    monkeypatch.setattr(
        SlippageProtectionEngine,
        "validate_transaction_slippage",
        _validate,
    )

    with pytest.raises(DexError):
        await handler.execute_swap(1, ["a", "b"])
    assert called["count"] == 1
