import asyncio
import pytest

import slippage_protection
import config

from exceptions import PriceManipulationError
from slippage_protection import (
    MarketConditions,
    SlippageParams,
    SlippageProtectionEngine,
    MIN_TOLERANCE_PERCENT,
    ZERO_SLIPPAGE_MSG,
    calculate_dynamic_slippage,
)
from observability.metrics import SLIPPAGE_CHECKS, SLIPPAGE_REJECTED


@pytest.mark.asyncio
async def test_check_within_tolerance(monkeypatch):
    params = SlippageParams(tolerance_percent=2.0, data_api="http://test")
    engine = SlippageProtectionEngine(params)

    async def fake_fetch() -> MarketConditions:
        return MarketConditions(price=100.0, liquidity=50.0, volatility=0.1)

    monkeypatch.setattr(engine, "_fetch_market_data", fake_fetch)
    start = SLIPPAGE_CHECKS._value.get()
    await engine.check(101.0, 10)
    assert SLIPPAGE_CHECKS._value.get() == start + 1


@pytest.mark.asyncio
async def test_check_rejects_on_slippage(monkeypatch):
    params = SlippageParams(tolerance_percent=1.0, data_api="http://test")
    engine = SlippageProtectionEngine(params)

    async def fake_fetch() -> MarketConditions:
        return MarketConditions(price=110.0, liquidity=100.0, volatility=0.1)

    monkeypatch.setattr(engine, "_fetch_market_data", fake_fetch)
    start = SLIPPAGE_REJECTED._value.get()
    with pytest.raises(PriceManipulationError):
        await engine.check(100.0, 10)
    assert SLIPPAGE_REJECTED._value.get() == start + 1


@pytest.mark.asyncio
async def test_check_warns_on_liquidity(monkeypatch):
    params = SlippageParams(tolerance_percent=5.0, data_api="http://test")
    engine = SlippageProtectionEngine(params)
    warnings: list[str] = []

    async def fake_fetch() -> MarketConditions:
        return MarketConditions(price=100.0, liquidity=5.0, volatility=0.1)

    monkeypatch.setattr(engine, "_fetch_market_data", fake_fetch)
    monkeypatch.setattr(
        slippage_protection,
        "logger",
        type(
            "L",
            (),
            {
                "warning": lambda msg, *a, **k: warnings.append(msg),
                "info": lambda *a, **k: None,
            },
        ),
    )
    await engine.check(100.0, 10)
    assert warnings


def test_analyze_market_conditions_classification():
    engine = SlippageProtectionEngine(SlippageParams(1.0, None))
    assert (
        engine.analyze_market_conditions(MarketConditions(100.0, 100.0, 0.6))
        == "volatile"
    )
    assert (
        engine.analyze_market_conditions(MarketConditions(100.0, 5.0, 0.1))
        == "illiquid"
    )
    assert (
        engine.analyze_market_conditions(MarketConditions(100.0, 50.0, 0.1)) == "stable"
    )


def test_calculate_dynamic_slippage():
    assert calculate_dynamic_slippage(0.1, 0.2) == 0.1 * 1.2


def test_calculate_protected_slippage_and_validation(monkeypatch):
    monkeypatch.setattr(config, "MAX_SLIPPAGE_BPS", 50)
    expected = 1000
    min_out = SlippageProtectionEngine.calculate_protected_slippage(expected)
    assert min_out == 995
    SlippageProtectionEngine.validate_transaction_slippage(expected, min_out)
    with pytest.raises(PriceManipulationError):
        SlippageProtectionEngine.validate_transaction_slippage(expected, 900)


def test_init_enforces_minimum_tolerance():
    params = SlippageParams(tolerance_percent=0.01, data_api=None)
    engine = SlippageProtectionEngine(params)
    assert engine.params.tolerance_percent == MIN_TOLERANCE_PERCENT


def test_zero_slippage_transaction_rejected(monkeypatch):
    monkeypatch.setattr(config, "MAX_SLIPPAGE_BPS", 50)
    with pytest.raises(PriceManipulationError, match=ZERO_SLIPPAGE_MSG):
        SlippageProtectionEngine.validate_transaction_slippage(1000, 1000)


@pytest.mark.asyncio
async def test_check_rejects_with_zero_tolerance(monkeypatch):
    monkeypatch.setattr(slippage_protection, "MIN_TOLERANCE_PERCENT", 0.0)
    params = SlippageParams(tolerance_percent=0.0, data_api="http://test")
    engine = SlippageProtectionEngine(params)

    async def fake_fetch() -> MarketConditions:
        return MarketConditions(price=101.0, liquidity=50.0, volatility=0.1)

    monkeypatch.setattr(engine, "_fetch_market_data", fake_fetch)
    with pytest.raises(PriceManipulationError):
        await engine.check(100.0, 10)


@pytest.mark.asyncio
async def test_large_trade_amount_triggers_penalty(monkeypatch):
    params = SlippageParams(tolerance_percent=5.0, data_api="http://test")
    engine = SlippageProtectionEngine(params)
    warnings: list[str] = []

    async def fake_fetch() -> MarketConditions:
        return MarketConditions(price=100.0, liquidity=10.0, volatility=0.1)

    monkeypatch.setattr(engine, "_fetch_market_data", fake_fetch)
    monkeypatch.setattr(
        slippage_protection,
        "logger",
        type(
            "L",
            (),
            {
                "warning": lambda msg, *a, **k: warnings.append(msg),
                "info": lambda *a, **k: None,
            },
        ),
    )
    await engine.check(100.0, 20)
    assert any("exceeds liquidity" in w for w in warnings)


def test_dynamic_slippage_high_volatility():
    result = calculate_dynamic_slippage(0.2, 0.8)
    assert result == pytest.approx(0.2 * 1.8)
