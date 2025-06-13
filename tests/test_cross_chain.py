import asyncio
import pytest

from cross_chain import (
    LayerZeroBridge,
    CCIPBridge,
    WormholeBridge,
    BridgeError,
)


class DummyService:
    async def sign_and_send_transaction(self, tx, timeout=120, retries=3):
        return {"hash": "0x1"}


@pytest.mark.asyncio
@pytest.mark.parametrize("bridge_cls", [LayerZeroBridge, CCIPBridge, WormholeBridge])
async def test_bridge_send(bridge_cls):
    service = DummyService()
    bridge = bridge_cls(service)
    result = await bridge.send("a", 1, "chain", "addr")
    assert result == {"hash": "0x1"}


@pytest.mark.asyncio
@pytest.mark.parametrize("bridge_cls", [LayerZeroBridge, CCIPBridge, WormholeBridge])
async def test_bridge_send_error(bridge_cls):
    class FailingService(DummyService):
        async def sign_and_send_transaction(self, tx, timeout=120, retries=3):
            raise RuntimeError("fail")

    bridge = bridge_cls(FailingService())
    with pytest.raises(BridgeError):
        await bridge.send("a", 1, "chain", "addr")
