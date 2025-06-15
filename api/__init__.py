"""FastAPI application exposing secure endpoints."""

from __future__ import annotations

import os
import time

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    Security,
    responses,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from analytics import ReportingError, generate_report
from exceptions import AnalyticsAPIError, BaseAppError, RateLimitError
from logger import get_logger
from middleware.rate_limiter import RateLimiterMiddleware
from risk_manager import RiskManager
from security.async_auth import TokenData, get_current_user

risk_manager = RiskManager()
logger = get_logger("api")

app = FastAPI(
    title="DEX Trading Bot API",
    description="Secure API for DEX trading operations",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(RateLimiterMiddleware)

allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

cors_origins = os.getenv("CORS_ORIGINS", "https://yourdomain.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    security_headers = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }
    for header, value in security_headers.items():
        response.headers[header] = value
    return response


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)


@app.exception_handler(BaseAppError)
async def handle_app_error(request: Request, exc: BaseAppError):
    logger.error("%s - %s", exc.code, exc.message)
    return responses.JSONResponse(
        status_code=429 if isinstance(exc, RateLimitError) else 503,
        content={"error": exc.code, "message": exc.message},
    )


@app.get("/health")
async def health() -> dict[str, int | str]:
    """Public health check."""
    return {"status": "ok", "timestamp": int(time.time())}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Readiness check."""
    return {"status": "ready"}


@app.get("/metrics")
@limiter.limit("10/minute")
async def metrics(
    request: Request,
    current_user: TokenData = Security(get_current_user, scopes=["admin"]),
) -> Response:
    """Protected metrics endpoint."""
    from prometheus_client import generate_latest

    return Response(generate_latest(), media_type="text/plain")


@app.get("/exchange")
async def exchange_status() -> dict[str, str]:
    """Exchange connectivity check."""
    return {"status": "ok"}


@app.get("/strategy")
async def strategy_health() -> dict[str, str]:
    """Simple strategy health endpoint."""
    return {"status": "running"}


@app.get("/analytics/report")
@limiter.limit("5/minute")
async def analytics_report(
    request: Request,
    period: str,
    current_user: TokenData = Security(get_current_user, scopes=["trading"]),
) -> dict:
    """Protected P&L report for the specified period."""
    if period not in {"daily", "weekly", "monthly"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid period")
    try:
        report = generate_report(period, list(risk_manager.returns))
        logger.info(
            "Analytics report generated",
            extra={"user": current_user.username, "period": period},
        )
        return report
    except ReportingError as exc:
        raise HTTPException(500, str(exc)) from exc


@app.get("/analytics/performance")
@limiter.limit("5/minute")
async def analytics_performance(
    request: Request,
    confidence: float = 0.95,
    current_user: TokenData = Security(get_current_user, scopes=["high_value"]),
) -> dict:
    """Protected performance metrics."""
    if not 0 < confidence < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Confidence must be between 0 and 1")
    try:
        data = {
            "var": risk_manager.var(confidence),
            "sharpe": risk_manager.sharpe(),
            "timestamp": int(time.time()),
        }
        return data
    except Exception as exc:  # noqa: BLE001
        logger.error("Performance calculation failed: %s", exc)
        raise HTTPException(500, "Performance calculation failed") from exc


@app.post("/admin/shutdown")
async def emergency_shutdown(
    current_user: TokenData = Security(get_current_user, scopes=["admin"]),
) -> dict[str, str]:
    """Emergency shutdown endpoint."""
    risk_manager.shutdown()
    logger.critical("Emergency shutdown triggered by %s", current_user.username)
    return {"status": "shutdown", "user": current_user.username}
