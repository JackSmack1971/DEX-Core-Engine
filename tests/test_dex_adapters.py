import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from dex_protocols import UniswapV3, Curve, Balancer
from exceptions import DexError
from web3_service import TransactionFailedError


@pytest.mark.asyncio
async def test_uniswap_v3_quote_and_swap(monkeypatch):
    service = MagicMock()
    service.account = MagicMock(address="0xabc")
    service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    service.sign_and_send_transaction = AsyncMock(
        return_value={"transactionHash": b"\x01"}
    )
    contract = MagicMock()
    service.get_contract.return_value = contract

    contract.functions.quoteExactInputSingle.return_value = MagicMock(
        call=MagicMock(return_value=123)
    )
    contract.functions.exactInputSingle.return_value = MagicMock(
        build_transaction=MagicMock(return_value={"tx": 1})
    )

    async def fake_to_thread(func, *args, **kwargs):
        return func()

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    dex = UniswapV3(service, "0xquoter", "0xrouter")
    dex._circuit.call = lambda func, *a, **kw: func(*a, **kw)

    quote = await dex.get_quote("0xa", "0xb", 1)
    assert quote == 123

    tx = await dex.execute_swap(1, ["0xa", "0xb"])
    assert tx == "01"
    service.sign_and_send_transaction.assert_awaited_once()


@pytest.mark.asyncio
async def test_uniswap_v3_swap_error(monkeypatch):
    service = MagicMock()
    service.account = MagicMock(address="0xabc")
    service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    contract = MagicMock()
    service.get_contract.return_value = contract

    contract.functions.quoteExactInputSingle.return_value = MagicMock(
        call=MagicMock(return_value=123)
    )
    contract.functions.exactInputSingle.return_value = MagicMock(
        build_transaction=MagicMock(return_value={"tx": 1})
    )

    async def fail_tx(_):
        raise TransactionFailedError("fail")

    service.sign_and_send_transaction = AsyncMock(side_effect=fail_tx)

    async def fake_to_thread(func, *args, **kwargs):
        return func()

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    dex = UniswapV3(service, "0xquoter", "0xrouter")
    dex._circuit.call = lambda func, *a, **kw: func(*a, **kw)

    with pytest.raises(DexError):
        await dex.execute_swap(1, ["0xa", "0xb"])


@pytest.mark.asyncio
async def test_curve_quote_and_swap(monkeypatch):
    service = MagicMock()
    service.account = MagicMock(address="0xabc")
    service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    service.sign_and_send_transaction = AsyncMock(
        return_value={"transactionHash": b"\x02"}
    )
    contract = MagicMock()
    service.get_contract.return_value = contract

    contract.functions.get_dy.return_value = MagicMock(
        call=MagicMock(return_value=456)
    )
    contract.functions.exchange.return_value = MagicMock(
        build_transaction=MagicMock(return_value={"tx": 1})
    )

    async def fake_to_thread(func, *args, **kwargs):
        return func()

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    dex = Curve(service, "0xpool", {"0xa": 0, "0xb": 1})
    dex._circuit.call = lambda func, *a, **kw: func(*a, **kw)

    quote = await dex.get_quote("0xa", "0xb", 1)
    assert quote == 456

    tx = await dex.execute_swap(1, ["0xa", "0xb"])
    assert tx == "02"
    service.sign_and_send_transaction.assert_awaited_once()


@pytest.mark.asyncio
async def test_balancer_quote_and_swap(monkeypatch):
    service = MagicMock()
    service.account = MagicMock(address="0xabc")
    service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    service.sign_and_send_transaction = AsyncMock(
        return_value={"transactionHash": b"\x03"}
    )
    contract = MagicMock()
    service.get_contract.return_value = contract

    contract.functions.queryBatchSwap.return_value = MagicMock(
        call=MagicMock(return_value=[0, -789])
    )
    contract.functions.swap.return_value = MagicMock(
        build_transaction=MagicMock(return_value={"tx": 1})
    )

    async def fake_to_thread(func, *args, **kwargs):
        return func()

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    dex = Balancer(service, "0xvault", "0xpool")
    dex._circuit.call = lambda func, *a, **kw: func(*a, **kw)

    quote = await dex.get_quote("0xa", "0xb", 1)
    assert quote == 789

    tx = await dex.execute_swap(1, ["0xa", "0xb"])
    assert tx == "03"
    service.sign_and_send_transaction.assert_awaited_once()



