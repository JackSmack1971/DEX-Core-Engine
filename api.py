"""FastAPI application exposing health endpoints."""

from __future__ import annotations

from fastapi import FastAPI, Request, responses

from analytics import ReportingError, generate_report
from exceptions import (
    AnalyticsAPIError,
    BaseAppError,
    RateLimitError,
)
from risk_manager import RiskManager

from middleware.rate_limiter import RateLimiterMiddleware
from prometheus_client import generate_latest
from logger import get_logger

risk_manager = RiskManager()

logger = get_logger("api")

app = FastAPI()
app.add_middleware(RateLimiterMiddleware)


@app.exception_handler(BaseAppError)
async def handle_app_error(request: Request, exc: BaseAppError):
    logger.error("%s - %s", exc.code, exc.message)
    return responses.JSONResponse(
        status_code=429 if isinstance(exc, RateLimitError) else 503,
        content={"error": exc.code, "message": exc.message},
    )


@app.get("/health")
async def health():
    """Liveness check."""
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    """Readiness check."""
    return {"status": "ready"}


@app.get("/metrics")
async def metrics() -> responses.Response:
    """Prometheus metrics endpoint."""
    return responses.Response(generate_latest(), media_type="text/plain")


@app.get("/exchange")
async def exchange_status():
    """Exchange connectivity check."""
    return {"status": "ok"}


@app.get("/strategy")
async def strategy_health():
    """Simple strategy health endpoint."""
    return {"status": "running"}


@app.get("/analytics/report")
async def analytics_report(period: str) -> dict:
    """Return a P&L report for the specified period."""
    if period not in {"daily", "weekly", "monthly"}:
        raise AnalyticsAPIError("invalid period")
    try:
        report = generate_report(period, list(risk_manager.returns))
    except ReportingError as exc:
        logger.error("report failed: %s", exc)
        raise AnalyticsAPIError(str(exc)) from exc
    logger.info("report", extra={"metadata": report})
    return report


@app.get("/analytics/performance")
async def analytics_performance(confidence: float = 0.95) -> dict:
    """Return risk metrics like VaR and Sharpe ratio."""
    if not 0 < confidence < 1:
        raise AnalyticsAPIError("confidence must be between 0 and 1")
    try:
        data = {
            "var": risk_manager.var(confidence),
            "sharpe": risk_manager.sharpe(),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("performance failed: %s", exc)
        raise AnalyticsAPIError(str(exc)) from exc
    logger.info("performance", extra={"metadata": data})
    return data

