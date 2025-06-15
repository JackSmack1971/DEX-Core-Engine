import pytest
from unittest.mock import MagicMock, patch
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


def test_retry_updates_nonce_and_resends():
    service = _mock_service()
    service.web3.eth.get_transaction_count.side_effect = [6]
    service.web3.eth.wait_for_transaction_receipt.side_effect = [TimeExhausted, {"status": 1}]
    tx = {"nonce": 5}
    with patch("random.uniform", return_value=0), patch("time.sleep") as sleep_mock:
        receipt = asyncio.run(service.sign_and_send_transaction(tx, timeout=0.1, retries=2))
    assert receipt["status"] == 1
    # sign/send called twice with updated nonce
    assert service.web3.eth.account.sign_transaction.call_count == 2
    assert service.web3.eth.send_raw_transaction.call_count == 2
    # nonce should be refreshed after first timeout
    assert service.web3.eth.get_transaction_count.call_count == 1
    second_nonce = service.web3.eth.account.sign_transaction.call_args_list[1][0][0]["nonce"]
    assert second_nonce == 6
    sleep_mock.assert_called_once_with(0.1)


def test_timeout_after_all_retries():
    service = _mock_service()
    service.web3.eth.get_transaction_count.side_effect = [1, 2, 3]
    service.web3.eth.send_raw_transaction.return_value = b"hash"
    service.web3.eth.wait_for_transaction_receipt.side_effect = TimeExhausted
    with patch("random.uniform", return_value=0), patch("time.sleep") as sleep_mock:
        with pytest.raises(TransactionTimeoutError) as exc:
            asyncio.run(service.sign_and_send_transaction({}, timeout=0.1))
    assert "timed out" in str(exc.value)
    # three attempts -> two sleeps
    assert sleep_mock.call_count == 2
    # nonce fetched once initially and twice more for retries
    assert service.web3.eth.get_transaction_count.call_count == 3


def test_init_successful_connection():
    with patch("web3_service.Web3") as Web3Mock, patch("web3_service.HTTPProvider"), patch(
        "web3_service.geth_poa_middleware"
    ), patch("web3_service.SecureKeyManager") as KM, patch("web3_service.secure_zero_memory") as zero:
        web3_instance = MagicMock()
        Web3Mock.return_value = web3_instance
        web3_instance.is_connected.return_value = True
        eth = MagicMock()
        eth.account.from_key.return_value = MagicMock(address="0xabc", key="key")
        web3_instance.eth = eth
        KM.return_value.decrypt_private_key.return_value = "plainkey"
        svc = Web3Service("http://rpc", "encrypted")
    assert svc.web3 is web3_instance
    assert svc.account.address == "0xabc"
    zero.assert_called_once()


def test_init_connection_failure():
    with patch("web3_service.Web3") as Web3Mock, patch("web3_service.HTTPProvider"), patch(
        "web3_service.geth_poa_middleware"
    ):
        web3_instance = MagicMock()
        Web3Mock.return_value = web3_instance
        web3_instance.is_connected.return_value = False
        with pytest.raises(ConnectionError):
            Web3Service("http://rpc", "encrypted")
