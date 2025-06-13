import asyncio
from unittest.mock import AsyncMock

import pytest

from cross_chain import LayerZeroBridge, BridgeError


class DummyService:
    async def sign_and_send_transaction(self, tx, timeout=120, retries=3):
        return {"hash": "0x1"}


@pytest.mark.asyncio
async def test_bridge_send():
    service = DummyService()
    bridge = LayerZeroBridge(service)
    result = await bridge.send("a", 1, "chain", "addr")
    assert result == {"hash": "0x1"}


@pytest.mark.asyncio
async def test_bridge_send_error():
    class FailingService(DummyService):
        async def sign_and_send_transaction(self, tx, timeout=120, retries=3):
            raise RuntimeError("fail")

    bridge = LayerZeroBridge(FailingService())
    with pytest.raises(BridgeError):
        await bridge.send("a", 1, "chain", "addr")
