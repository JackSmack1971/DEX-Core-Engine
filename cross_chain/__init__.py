"""Cross-chain bridge interfaces."""

from __future__ import annotations

from abc import ABC

from web3_service import Web3Service
from .bridge_provider import BridgeProvider, HttpBridgeProvider, BridgeProviderError


class BridgeError(Exception):
    """Raised when bridging fails."""


class Bridge(ABC):
    """Bridge base class with common ``send`` implementation."""

    def __init__(self, service: Web3Service) -> None:
        self.service = service

    async def send(self, token: str, amount: int, dst_chain: str, address: str) -> str:
        """Bridge ``token`` to ``dst_chain``."""
        try:
            return await self.service.sign_and_send_transaction({"to": address, "value": amount})
        except Exception as exc:  # noqa: BLE001
            raise BridgeError(str(exc)) from exc


class LayerZeroBridge(Bridge):
    """Bridge implementation using the LayerZero network."""
    pass


class CCIPBridge(Bridge):
    """Bridge implementation using CCIP."""
    pass


class WormholeBridge(Bridge):
    """Bridge implementation using Wormhole."""
    pass


__all__ = [
    "Bridge",
    "LayerZeroBridge",
    "CCIPBridge",
    "WormholeBridge",
    "BridgeError",
    "BridgeProvider",
    "HttpBridgeProvider",
    "BridgeProviderError",
]
