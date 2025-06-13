import pytest
from unittest.mock import AsyncMock

from flash_loans.arbitrage import FlashArbitrageExecutor, FlashArbitrageError
from flash_loans import FlashLoanProvider
from risk_manager import RiskManager
from web3_service import Web3Service


class DummyProvider(FlashLoanProvider):
    async def borrow(self, token: str, amount: int) -> str:
        return "borrow"

    async def repay(self, token: str, amount: int) -> str:
        return "repay"


def _service() -> Web3Service:
    svc = Web3Service.__new__(Web3Service)
    svc.sign_and_send_transaction = AsyncMock(return_value={"transactionHash": b"0x1"})
    return svc


@pytest.mark.asyncio
async def test_arbitrage_executor_success():
    service = _service()
    provider = DummyProvider(service)
    provider.borrow = AsyncMock(return_value="b")
    provider.repay = AsyncMock(return_value="r")

    async def trade(amount: int) -> str:
        return "tx"

    executor = FlashArbitrageExecutor(provider, service, RiskManager())
    tx = await executor.execute("tok", 1000.0, trade)
    assert tx == "tx"
    provider.borrow.assert_awaited_once()
    provider.repay.assert_awaited()


@pytest.mark.asyncio
async def test_arbitrage_executor_trade_fail():
    service = _service()
    provider = DummyProvider(service)
    provider.borrow = AsyncMock(return_value="b")
    provider.repay = AsyncMock(return_value="r")

    async def trade(amount: int) -> str:
        raise RuntimeError("fail")

    executor = FlashArbitrageExecutor(provider, service, RiskManager())
    with pytest.raises(FlashArbitrageError):
        await executor.execute("tok", 1000.0, trade)
    provider.repay.assert_awaited()
