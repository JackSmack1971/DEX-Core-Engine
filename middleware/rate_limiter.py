"""Simple IP based rate limiting middleware."""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import FastAPI, Request, Response, responses
from starlette.middleware.base import BaseHTTPMiddleware



class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Allow only N requests per minute per client IP."""

    instance: "RateLimiterMiddleware | None" = None

    def __init__(self, app: FastAPI, limit: int | None = None) -> None:
        super().__init__(app)
        env_limit = int(os.getenv("API_RATE_LIMIT", "100"))
        self.limit = limit or env_limit
        self.window = 60
        self._hits: defaultdict[str, Deque[float]] = defaultdict(deque)
        RateLimiterMiddleware.instance = self

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = request.client.host
        now = time.time()
        q = self._hits[ip]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return responses.JSONResponse(
                status_code=429,
                content={"error": "rate_limit", "message": "too many requests"},
            )
        q.append(now)
        return await call_next(request)

    @classmethod
    def get_instance(cls) -> "RateLimiterMiddleware":
        if cls.instance is None:
            raise RuntimeError("RateLimiterMiddleware not initialized")
        return cls.instance

    def reset(self) -> None:
        """Reset all tracked client request counters."""
        self._hits.clear()
