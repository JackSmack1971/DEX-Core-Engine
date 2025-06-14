import os
import asyncio
from types import SimpleNamespace

import pytest

from analytics import AnalyticsEngine, AnalyticsError
from risk_manager import RiskManager


class DummyResp:
    def __init__(self, rate: float) -> None:
        self.rate = rate

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return {"rates": {"USD": self.rate}}


class DummyClient:
    def __init__(self, rate: float) -> None:
        self.rate = rate

    async def __aenter__(self) -> "DummyClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        pass

    async def get(self, *_: str, **__: object) -> DummyResp:
        return DummyResp(self.rate)


@pytest.mark.asyncio
async def test_register_and_pnl(monkeypatch):
    os.environ["FX_API_URL"] = "http://test"
    os.environ["FX_API_KEY"] = "k"
    rm = RiskManager()
    engine = AnalyticsEngine(rm)
    monkeypatch.setattr(engine, "_circuit", SimpleNamespace(call=lambda f, *a, **k: f(*a, **k)))
    monkeypatch.setattr("httpx.AsyncClient", lambda timeout: DummyClient(1.0))
    await engine.register_asset("s1", "AAA", 1, 100, "EUR")
    await engine.update_price("AAA", 110, "EUR")
    realized, unreal = engine.pnl_per_strategy("s1")
    assert unreal == pytest.approx(10.0)
    engine.record_trade("s1", 5.0)
    realized, unreal = engine.pnl_per_strategy("s1")
    assert realized == 5.0


def test_ratios():
    rm = RiskManager()
    engine = AnalyticsEngine(rm)
    returns = [0.1, -0.05, 0.2, -0.1]
    bench = [0.05, 0.0, 0.1, -0.02]
    assert engine.win_rate(returns) == 0.5
    aw, al = engine.average_win_loss(returns)
    assert aw > 0 and al < 0
    assert engine.profit_factor(returns) > 1
    assert engine.max_drawdown(returns) < 0
    assert engine.sortino_ratio(returns) != 0
    assert engine.calmar_ratio(returns) != 0
    assert engine.information_ratio(returns, bench) != 0
    assert engine.beta(returns, bench) != 0
    assert engine.rolling(returns, 2) == pytest.approx([0.025, 0.075, 0.05])


@pytest.mark.asyncio
async def test_error_on_bad_window(monkeypatch):
    rm = RiskManager()
    engine = AnalyticsEngine(rm)
    with pytest.raises(AnalyticsError):
        engine.rolling([0.1], 0)

    monkeypatch.setattr(engine, "_circuit", SimpleNamespace(call=lambda f, *a, **k: f(*a, **k)))
    os.environ["FX_API_URL"] = "http://t"
    os.environ["FX_API_KEY"] = "k"
    monkeypatch.setattr("httpx.AsyncClient", lambda timeout: DummyClient(1.2))
    await engine.update_price("AAA", 1, "EUR")


@pytest.mark.asyncio
async def test_fetch_rate(monkeypatch):
    os.environ["FX_API_URL"] = "http://test"
    os.environ["FX_API_KEY"] = "k"
    rm = RiskManager()
    engine = AnalyticsEngine(rm)
    monkeypatch.setattr(engine, "_circuit", SimpleNamespace(call=lambda f, *a, **k: f(*a, **k)))
    monkeypatch.setattr("httpx.AsyncClient", lambda timeout: DummyClient(2.0))
    rate = await engine._fetch_rate("EUR", "USD")
    assert rate == 2.0


@pytest.mark.asyncio
async def test_fetch_rate_missing(monkeypatch):
    os.environ.pop("FX_API_URL", None)
    os.environ.pop("FX_API_KEY", None)
    rm = RiskManager()
    engine = AnalyticsEngine(rm)
    monkeypatch.setattr(engine, "_circuit", SimpleNamespace(call=lambda f, *a, **k: f(*a, **k)))
    with pytest.raises(AnalyticsError):
        await engine._fetch_rate("EUR", "USD")


@pytest.mark.asyncio
async def test_convert_price_same_currency():
    rm = RiskManager()
    engine = AnalyticsEngine(rm)
    price = await engine._convert_price(10.0, "USD")
    assert price == 10.0
