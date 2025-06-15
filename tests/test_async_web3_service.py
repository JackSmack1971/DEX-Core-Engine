import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from web3.exceptions import TimeExhausted

from async_web3_service import (
    AsyncWeb3Service,
    TransactionFailedError,
    TransactionTimeoutError,
)


def _mock_service() -> AsyncWeb3Service:
    service = AsyncWeb3Service.__new__(AsyncWeb3Service)
    service.web3 = MagicMock()
    eth = MagicMock()
    eth.get_transaction_count = AsyncMock(return_value=1)
    eth.send_transaction = AsyncMock(return_value=b"hash")
    eth.wait_for_transaction_receipt = AsyncMock(return_value={"status": 1})
    class _PriorityFee:
        def __await__(self):
            async def coro():
                return 1
            return coro().__await__()

    eth.max_priority_fee = _PriorityFee()
    eth.fee_history = AsyncMock(return_value={"baseFeePerGas": [1]})
    service.web3.eth = eth
    service.account = MagicMock(address="0xabc")
    return service


@pytest.mark.asyncio
async def test_sign_and_send_success():
    service = _mock_service()
    receipt = await service.sign_and_send_transaction({})
    assert receipt["status"] == 1
    args, _ = service.web3.eth.send_transaction.call_args
    assert "maxFeePerGas" in args[0]


@pytest.mark.asyncio
async def test_sign_and_send_failure_status_zero():
    service = _mock_service()
    service.web3.eth.wait_for_transaction_receipt.return_value = {"status": 0}
    with pytest.raises(TransactionFailedError):
        await service.sign_and_send_transaction({})


@pytest.mark.asyncio
async def test_sign_and_send_timeout_then_raises():
    service = _mock_service()
    service.web3.eth.wait_for_transaction_receipt.side_effect = TimeExhausted
    with pytest.raises(TransactionTimeoutError):
        await service.sign_and_send_transaction({}, timeout=0.1, retries=2)


@pytest.mark.asyncio
async def test_sign_and_send_timeout_then_success():
    service = _mock_service()
    service.web3.eth.wait_for_transaction_receipt.side_effect = [
        TimeExhausted,
        {"status": 1},
    ]
    receipt = await service.sign_and_send_transaction({}, timeout=0.1, retries=2)
    assert receipt["status"] == 1
