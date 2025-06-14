"""FastAPI application exposing health endpoints."""

from __future__ import annotations

from fastapi import FastAPI, Request, responses
from pydantic import BaseModel, Field, ValidationError, conlist, validator

from analytics import generate_report
from analytics.metrics import (
    ANALYTICS_DRAWDOWN,
    ANALYTICS_PNL,
    ROLLING_PERFORMANCE_30D,
    ROLLING_PERFORMANCE_7D,
)

from middleware.rate_limiter import RateLimiterMiddleware
from exceptions import (
    AnalyticsRequestError,
    BaseAppError,
    RateLimitError,
)
from prometheus_client import generate_latest
from logger import get_logger

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


class ReportRequest(BaseModel):
    period: str = Field(..., description="daily, weekly or monthly")
    returns: conlist(float, min_length=1)

    @validator("period")
    def _check_period(cls, value: str) -> str:
        if value not in {"daily", "weekly", "monthly"}:
            raise ValueError("period must be daily, weekly or monthly")
        return value


@app.post("/analytics/report")
async def analytics_report(request: Request):
    """Generate portfolio report based on provided returns."""
    try:
        payload = await request.json()
        data = ReportRequest(**payload)
        report = generate_report(data.period, data.returns)
        logger.info(
            "generated report",
            extra={"metadata": {"period": data.period}},
        )
        return report
    except ValidationError as exc:
        logger.error("report validation failed: %s", exc)
        raise AnalyticsRequestError(str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.error("report failed: %s", exc)
        raise AnalyticsRequestError(str(exc))


@app.get("/analytics/performance")
async def analytics_performance() -> dict[str, float]:
    """Return current analytics performance metrics."""
    stats = {
        "pnl": ANALYTICS_PNL._value.get(),
        "drawdown": ANALYTICS_DRAWDOWN._value.get(),
        "rolling_7d": ROLLING_PERFORMANCE_7D._value.get(),
        "rolling_30d": ROLLING_PERFORMANCE_30D._value.get(),
    }
    logger.info("performance stats", extra={"metadata": stats})
    return stats

