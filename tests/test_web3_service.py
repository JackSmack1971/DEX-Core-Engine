import pytest
from unittest.mock import MagicMock

from web3.exceptions import TimeExhausted
import asyncio

from web3_service import Web3Service, TransactionFailedError, TransactionTimeoutError


def _mock_service() -> Web3Service:
    service = Web3Service.__new__(Web3Service)
    service.web3 = MagicMock()
    service.account = MagicMock(address="0xabc", key="key")
    service.web3.eth.get_transaction_count.return_value = 1
    service.web3.eth.account.sign_transaction.return_value = MagicMock(rawTransaction=b"tx")
    return service


def test_sign_and_send_success():
    service = _mock_service()
    receipt = {"status": 1}
    service.web3.eth.send_raw_transaction.return_value = b"hash"
    service.web3.eth.wait_for_transaction_receipt.return_value = receipt

    result = asyncio.run(service.sign_and_send_transaction({}))
    assert result is receipt


def test_sign_and_send_failure_status_zero():
    service = _mock_service()
    receipt = {"status": 0}
    service.web3.eth.send_raw_transaction.return_value = b"hash"
    service.web3.eth.wait_for_transaction_receipt.return_value = receipt

    with pytest.raises(TransactionFailedError):
        asyncio.run(service.sign_and_send_transaction({}))


def test_sign_and_send_timeout_then_raises():
    service = _mock_service()
    service.web3.eth.send_raw_transaction.return_value = b"hash"
    service.web3.eth.wait_for_transaction_receipt.side_effect = TimeExhausted

    with pytest.raises(TransactionTimeoutError):
        asyncio.run(service.sign_and_send_transaction({}, timeout=0.1, retries=2))


def test_sign_and_send_timeout_then_success():
    service = _mock_service()
    receipt = {"status": 1}
    service.web3.eth.send_raw_transaction.return_value = b"hash"
    service.web3.eth.wait_for_transaction_receipt.side_effect = [TimeExhausted, receipt]

    result = asyncio.run(service.sign_and_send_transaction({}, timeout=0.1, retries=2))
    assert result is receipt
