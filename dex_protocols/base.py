from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from exceptions import DexError, ServiceUnavailableError
from logger import get_logger
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async


@dataclass
class LiquidityInfo:
    """Information about pair liquidity and price impact."""

    liquidity: float
    price_impact: float


class BaseDEXProtocol(ABC):
    """Abstract base class for DEX protocol implementations."""

    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__.lower())
        self._circuit = CircuitBreaker()

    async def get_quote(self, token_in: str, token_out: str, amount_in: int) -> float:
        """Return ``token_out`` amount received for ``amount_in`` of ``token_in``."""
        self._validate_tokens(token_in, token_out)
        if amount_in <= 0:
            raise DexError("amount_in must be positive")
        try:
            return await self._circuit.call(
                retry_async, self._get_quote, token_in, token_out, amount_in
            )
        except ServiceUnavailableError as exc:
            self.logger.error("Quote circuit open: %s", exc)
            return 0.0
        except DexError:
            raise
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Quote failed: %s", exc)
            return 0.0

    async def execute_swap(self, amount_in: int, route: List[str]) -> str:
        """Execute a swap along ``route`` and return the transaction hash."""
        if amount_in <= 0 or not route or any(not r for r in route):
            raise DexError("invalid swap parameters")
        try:
            return await self._circuit.call(
                retry_async, self._execute_swap, amount_in, route
            )
        except ServiceUnavailableError as exc:
            self.logger.error("Swap circuit open: %s", exc)
            raise DexError("service unavailable") from exc
        except DexError:
            raise
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Swap failed: %s", exc)
            raise DexError(str(exc)) from exc

    async def get_best_route(
        self, token_in: str, token_out: str, amount_in: int
    ) -> List[str]:
        """Return the optimal swap route."""
        self._validate_tokens(token_in, token_out)
        if amount_in <= 0:
            raise DexError("amount_in must be positive")
        try:
            return await self._circuit.call(
                retry_async, self._get_best_route, token_in, token_out, amount_in
            )
        except ServiceUnavailableError as exc:
            self.logger.error("Route circuit open: %s", exc)
            return []
        except DexError:
            raise
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Route lookup failed: %s", exc)
            return []

    def _validate_tokens(self, token_in: str, token_out: str) -> None:
        if not token_in or not token_out:
            raise DexError("token addresses required")

    @abstractmethod
    async def _get_quote(
        self, token_in: str, token_out: str, amount_in: int
    ) -> float:
        """Query the protocol for a price quote."""

    @abstractmethod
    async def _execute_swap(self, amount_in: int, route: List[str]) -> str:
        """Perform the swap on-chain."""

    @abstractmethod
    async def _get_best_route(
        self, token_in: str, token_out: str, amount_in: int
    ) -> List[str]:
        """Compute the best swap route."""

    async def get_liquidity_info(
        self, token_in: str, token_out: str, amount_in: int
    ) -> LiquidityInfo:
        """Return liquidity and price impact for ``amount_in``."""
        return LiquidityInfo(0.0, 0.0)


__all__ = ["BaseDEXProtocol", "LiquidityInfo"]
