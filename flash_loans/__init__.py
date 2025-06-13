from __future__ import annotations

"""Flash loan utilities."""

from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from web3_service import Web3Service


class FlashLoanError(Exception):
    """Raised when flash loan execution fails."""


class FlashLoanProvider(ABC):
    """Abstract flash loan provider interface."""

    def __init__(self, service: Web3Service) -> None:
        self.service = service

    @abstractmethod
    async def borrow(self, token: str, amount: int) -> str:
        """Borrow ``amount`` of ``token`` and return tx hash."""

    @abstractmethod
    async def repay(self, token: str, amount: int) -> str:
        """Repay ``amount`` of ``token`` and return tx hash."""


class FlashLoanExecutor:
    """Coordinate flash loan borrow, trade, and repay steps."""

    def __init__(self, provider: FlashLoanProvider) -> None:
        self.provider = provider

    async def execute(
        self,
        token: str,
        amount: int,
        trade_fn: Callable[[], Awaitable[str]],
    ) -> str:
        await self.provider.borrow(token, amount)
        try:
            tx = await trade_fn()
        except Exception as exc:  # noqa: BLE001
            await self.provider.repay(token, amount)
            raise FlashLoanError(str(exc)) from exc
        await self.provider.repay(token, amount)
        return tx


__all__ = ["FlashLoanProvider", "FlashLoanExecutor", "FlashLoanError"]
