import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from batcher import Batcher
from exceptions import BatcherError, DexError


@pytest.mark.asyncio
async def test_batcher_execute_success(monkeypatch):
    service = MagicMock()
    service.account = MagicMock(address="0xabc")
    service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    multicall = MagicMock()
    multicall.functions.multicall.return_value = MagicMock(
        build_transaction=MagicMock(return_value={"tx": 1})
    )
    service.get_contract.return_value = multicall
    service.sign_and_send_transaction = AsyncMock(
        return_value={"transactionHash": b"\x01"}
    )
    batcher = Batcher(service, "0xbatch")
    batcher._circuit.call = lambda func, *a, **kw: func(*a, **kw)

    tx = await batcher.execute([b"a", b"b"], reorder=True)
    assert tx == "01"
    service.sign_and_send_transaction.assert_awaited_once()


@pytest.mark.asyncio
async def test_batcher_execute_failure(monkeypatch):
    service = MagicMock()
    service.account = MagicMock(address="0xabc")
    service.web3 = MagicMock(eth=MagicMock(gas_price=1))
    multicall = MagicMock()
    multicall.functions.multicall.return_value = MagicMock(
        build_transaction=MagicMock(return_value={"tx": 1})
    )
    service.get_contract.return_value = multicall
    service.sign_and_send_transaction = AsyncMock(
        side_effect=Exception("fail")
    )
    batcher = Batcher(service, "0xbatch")
    batcher._circuit.call = lambda func, *a, **kw: func(*a, **kw)

    with pytest.raises(BatcherError):
        await batcher.execute([b"a"])


@pytest.mark.asyncio
async def test_batcher_validate_calls(monkeypatch):
    batcher = Batcher.__new__(Batcher)
    with pytest.raises(DexError):
        await Batcher.execute(batcher, [])
