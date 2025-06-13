import asyncio
from unittest.mock import AsyncMock

import pytest

from flash_loans import FlashLoanExecutor, FlashLoanProvider, FlashLoanError


class DummyProvider(FlashLoanProvider):
    async def borrow(self, token: str, amount: int) -> str:
        return "borrow"

    async def repay(self, token: str, amount: int) -> str:
        return "repay"


@pytest.mark.asyncio
async def test_flash_loan_executor():
    provider = DummyProvider.__new__(DummyProvider)
    DummyProvider.__init__(provider, service=None)  # type: ignore[arg-type]
    provider.borrow = AsyncMock(return_value="borrow")
    provider.repay = AsyncMock(return_value="repay")

    async def trade() -> str:
        return "tx"

    executor = FlashLoanExecutor(provider)
    tx = await executor.execute("a", 1, trade)
    assert tx == "tx"
    provider.borrow.assert_awaited_once()
    provider.repay.assert_awaited()


@pytest.mark.asyncio
async def test_flash_loan_executor_handles_error():
    provider = DummyProvider.__new__(DummyProvider)
    DummyProvider.__init__(provider, service=None)  # type: ignore[arg-type]
    provider.borrow = AsyncMock(return_value="borrow")
    provider.repay = AsyncMock(return_value="repay")

    async def trade() -> str:
        raise RuntimeError("fail")

    executor = FlashLoanExecutor(provider)
    with pytest.raises(FlashLoanError):
        await executor.execute("a", 1, trade)
    provider.repay.assert_awaited()
