from __future__ import annotations

"""Cross-chain bridge interfaces."""

from abc import ABC, abstractmethod

from web3_service import Web3Service
from .bridge_provider import BridgeProvider, HttpBridgeProvider, BridgeProviderError


class BridgeError(Exception):
    """Raised when bridging fails."""


class Bridge(ABC):
    """Abstract bridge base class."""

    def __init__(self, service: Web3Service) -> None:
        self.service = service

    @abstractmethod
    async def send(self, token: str, amount: int, dst_chain: str, address: str) -> str:
        """Bridge ``token`` to ``dst_chain``."""


class LayerZeroBridge(Bridge):
    async def send(self, token: str, amount: int, dst_chain: str, address: str) -> str:
        try:
            return await self.service.sign_and_send_transaction({"to": address, "value": amount})
        except Exception as exc:  # noqa: BLE001
            raise BridgeError(str(exc)) from exc


class CCIPBridge(Bridge):
    async def send(self, token: str, amount: int, dst_chain: str, address: str) -> str:
        try:
            return await self.service.sign_and_send_transaction({"to": address, "value": amount})
        except Exception as exc:  # noqa: BLE001
            raise BridgeError(str(exc)) from exc


class WormholeBridge(Bridge):
    async def send(self, token: str, amount: int, dst_chain: str, address: str) -> str:
        try:
            return await self.service.sign_and_send_transaction({"to": address, "value": amount})
        except Exception as exc:  # noqa: BLE001
            raise BridgeError(str(exc)) from exc


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
