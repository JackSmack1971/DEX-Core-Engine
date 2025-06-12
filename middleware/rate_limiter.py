"""Simple IP based rate limiting middleware."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import Request, Response, responses
from starlette.middleware.base import BaseHTTPMiddleware



class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Allow only N requests per minute per client IP."""

    def __init__(self, app, limit: int = 100) -> None:
        super().__init__(app)
        self.limit = limit
        self.window = 60
        self._hits: defaultdict[str, Deque[float]] = defaultdict(deque)

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
