"""FastAPI application exposing health endpoints."""

from __future__ import annotations

from fastapi import FastAPI, Request, responses

from middleware.rate_limiter import RateLimiterMiddleware
from exceptions import BaseAppError, RateLimitError
from logger import logger

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

