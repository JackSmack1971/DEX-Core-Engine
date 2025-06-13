import asyncio

import pytest

import config
from exceptions import PriceManipulationError
from security import mev_protection


@pytest.mark.asyncio
async def test_protection_disabled(monkeypatch):
    monkeypatch.setattr(config, "MEV_PROTECTION_ENABLED", False)
    called = False

    async def fake_sim(*_a, **_kw):
        nonlocal called
        called = True
        return 1.0

    monkeypatch.setattr(mev_protection, "_simulate_price", fake_sim)
    result = await mev_protection.protect_transaction({}, 1.0)
    assert result is None
    assert not called


@pytest.mark.asyncio
async def test_protection_submits(monkeypatch):
    monkeypatch.setattr(config, "MEV_PROTECTION_ENABLED", True)
    monkeypatch.setattr(config, "FORK_RPC_URL", "fork")
    monkeypatch.setattr(config, "FLASHBOTS_URL", "flash")
    monkeypatch.setattr(config, "DEVIATION_THRESHOLD", 0.05)

    async def fake_sim(*_a, **_kw):
        return 1.0

    async def fake_submit(*_a, **_kw):
        return "ok"

    monkeypatch.setattr(mev_protection, "_simulate_price", fake_sim)
    monkeypatch.setattr(mev_protection, "_submit_flashbots", fake_submit)

    result = await mev_protection.protect_transaction({}, 1.0)
    assert result == "ok"


@pytest.mark.asyncio
async def test_price_deviation_raises(monkeypatch):
    monkeypatch.setattr(config, "MEV_PROTECTION_ENABLED", True)
    monkeypatch.setattr(config, "FORK_RPC_URL", "fork")
    monkeypatch.setattr(config, "FLASHBOTS_URL", None)
    monkeypatch.setattr(config, "DEVIATION_THRESHOLD", 0.05)

    async def fake_sim(*_a, **_kw):
        return 2.0

    monkeypatch.setattr(mev_protection, "_simulate_price", fake_sim)

    with pytest.raises(PriceManipulationError):
        await mev_protection.protect_transaction({}, 1.0)
