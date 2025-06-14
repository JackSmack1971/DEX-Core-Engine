"""Flash loan based arbitrage executor."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from risk_manager import RiskManager
from utils.retry import retry_async
from web3_service import Web3Service

from . import FlashLoanError, FlashLoanProvider


class FlashArbitrageError(Exception):
    """Raised when flash arbitrage execution fails."""


class FlashArbitrageExecutor:
    """Execute arbitrage trades using flash loans."""

    def __init__(
        self,
        provider: FlashLoanProvider,
        service: Web3Service,
        risk_manager: RiskManager | None = None,
    ) -> None:
        self.provider = provider
        self.service = service
        self.risk_manager = risk_manager or RiskManager()

    async def execute(
        self,
        token: str,
        capital: float,
        trade_fn: Callable[[int], Awaitable[str]],
        risk: float = 0.02,
        timeout: float = 30.0,
        retries: int = 3,
    ) -> str:
        if not token or capital <= 0 or risk <= 0:
            raise FlashArbitrageError("invalid arguments")
        amount = int(self.risk_manager.position_size(capital, risk))

        async def _borrow() -> str:
            return await asyncio.wait_for(
                self.provider.borrow(token, amount), timeout
            )

        async def _repay() -> str:
            return await asyncio.wait_for(
                self.provider.repay(token, amount), timeout
            )

        async def _trade() -> str:
            return await asyncio.wait_for(trade_fn(amount), timeout)

        await retry_async(_borrow, retries=retries)
        try:
            tx = await retry_async(_trade, retries=retries)
        except Exception as exc:  # noqa: BLE001
            await retry_async(_repay, retries=retries)
            raise FlashArbitrageError(str(exc)) from exc
        await retry_async(_repay, retries=retries)
        return tx


__all__ = ["FlashArbitrageExecutor", "FlashArbitrageError"]
