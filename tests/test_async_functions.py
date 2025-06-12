import os
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

os.environ.setdefault("RPC_URL", "http://localhost")
os.environ.setdefault("PRIVATE_KEY", "test")
os.environ.setdefault("WALLET_ADDRESS", "0x0000000000000000000000000000000000000005")
os.environ.setdefault("TOKEN0_ADDRESS", "0x0000000000000000000000000000000000000001")
os.environ.setdefault("TOKEN1_ADDRESS", "0x0000000000000000000000000000000000000002")
os.environ.setdefault("UNISWAP_V2_ROUTER", "0x0000000000000000000000000000000000000003")
os.environ.setdefault("SUSHISWAP_ROUTER", "0x0000000000000000000000000000000000000004")

from dex_handler import DEXHandler
from strategy import ArbitrageStrategy


@pytest.mark.asyncio
async def test_get_price_success(monkeypatch):
    handler = DEXHandler.__new__(DEXHandler)
    handler.contract = MagicMock()

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
    dex1 = MagicMock()
    dex2 = MagicMock()
    dex1.router_address = "dex1"
    dex2.router_address = "dex2"
    dex1.get_price = AsyncMock(return_value=1.0)
    dex2.get_price = AsyncMock(return_value=2.0)

    strategy = ArbitrageStrategy([dex1, dex2])
    strategy._check_profitability = MagicMock()

    async def stop_sleep(_):
        raise asyncio.CancelledError()

    monkeypatch.setattr(asyncio, "sleep", stop_sleep)

    with pytest.raises(asyncio.CancelledError):
        await strategy.run()

    strategy._check_profitability.assert_called_with(1.0, 2.0)
