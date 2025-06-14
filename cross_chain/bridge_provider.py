"""Bridge price providers for cross-chain arbitrage."""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx
from exceptions import ServiceUnavailableError
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async


class BridgeProviderError(Exception):
    """Raised when bridge price retrieval fails."""


class BridgeProvider(ABC):
    """Abstract bridge price provider."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    @abstractmethod
    async def get_price(self, token: str, chain: str) -> float:
        """Return ``token`` price on ``chain``."""


class HttpBridgeProvider(BridgeProvider):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url)
        self._circuit = CircuitBreaker()

    async def _fetch_price(self, token: str, chain: str) -> float:
        url = f"{self.base_url}/{chain}/{token}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        return float(data["price"])

    async def get_price(self, token: str, chain: str) -> float:
        if not token or not chain or not token.isalnum() or not chain.isalnum():
            raise BridgeProviderError("invalid parameters")
        try:
            return await self._circuit.call(
                retry_async, self._fetch_price, token, chain
            )
        except ServiceUnavailableError as exc:
            raise BridgeProviderError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise BridgeProviderError(str(exc)) from exc


__all__ = ["BridgeProvider", "HttpBridgeProvider", "BridgeProviderError"]
