from __future__ import annotations

"""Bridge price providers for cross-chain arbitrage."""

from abc import ABC, abstractmethod

import httpx


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
    async def get_price(self, token: str, chain: str) -> float:
        if not token or not chain:
            raise BridgeProviderError("invalid parameters")
        url = f"{self.base_url}/{chain}/{token}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
            return float(data["price"])
        except Exception as exc:  # noqa: BLE001
            raise BridgeProviderError(str(exc)) from exc


__all__ = ["BridgeProvider", "HttpBridgeProvider", "BridgeProviderError"]
