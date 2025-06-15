from __future__ import annotations

"""Asynchronous trade request validation utilities."""

import asyncio
import os
from dataclasses import dataclass

import httpx

from models.trade_requests import EnhancedTradeRequest
from utils.retry import retry_async
from logger import get_logger


logger = get_logger("async_validators")


class ValidationError(Exception):
    """Raised when a trade request fails validation."""


class RiskModelError(Exception):
    """Raised when risk scoring fails."""


@dataclass
class AsyncFinancialTransactionValidator:
    """Validate trade requests using an external risk model."""

    max_concurrent: int = int(os.getenv("VALIDATION_MAX_CONCURRENT", "5"))
    timeout: float = float(os.getenv("VALIDATION_TIMEOUT", "5.0"))
    threshold: float = float(os.getenv("RISK_THRESHOLD", "0.5"))

    def __post_init__(self) -> None:
        self._sem = asyncio.BoundedSemaphore(self.max_concurrent)

    async def score_risk(self, request: EnhancedTradeRequest) -> float:
        """Return a risk score for ``request`` between 0 and 1."""
        url = os.getenv("RISK_MODEL_URL")
        if not url:
            raise RiskModelError("missing model url")
        payload = request.model_dump()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return float(data.get("risk_score", 1.0))

    async def validate_request(self, request: EnhancedTradeRequest) -> bool:
        """Validate ``request`` asynchronously with retry and timeout."""
        if not isinstance(request, EnhancedTradeRequest):
            raise ValidationError("invalid request type")
        async with self._sem:
            try:
                score = await asyncio.wait_for(
                    retry_async(self.score_risk, request, retries=3),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError as exc:
                logger.error("Risk scoring timed out: %s", exc)
                raise RiskModelError("timeout") from exc
            except Exception as exc:  # noqa: BLE001 - propagate as custom error
                logger.error("Risk scoring failed: %s", exc)
                raise RiskModelError(str(exc)) from exc
        if score > self.threshold:
            raise ValidationError("risk score too high")
        return True
