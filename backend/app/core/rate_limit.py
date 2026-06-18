"""Lightweight in-process rate limiter.

V1 runs as a single Uvicorn process on a local machine, so an in-memory fixed
-window counter is sufficient and — crucially — does NOT perform any network I/O
in the request hot path. The previous implementation called a *synchronous*
Redis client from inside the async event loop on every request, which stalled
the whole server whenever Redis was slow or not running (the common case on a
local Windows dev box). Redis-backed limiting can return as a future enhancement.
"""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.i18n import t

# Paths that must never be throttled or wrapped (health checks, SSE stream).
_EXEMPT_PREFIXES = ("/health", "/docs", "/redoc", "/openapi", "/static")
_EXEMPT_SUFFIXES = ("/logs/stream",)

# client+path -> (window_start_epoch, count)
_WINDOW = 60.0
_buckets: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])


def _is_exempt(path: str) -> bool:
    return path.startswith(_EXEMPT_PREFIXES) or path.endswith(_EXEMPT_SUFFIXES)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window limiter, per client IP + path, fully in-memory."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if _is_exempt(path):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        key = f"{client}:{path}"
        now = time.time()
        bucket = _buckets[key]
        if now - bucket[0] >= _WINDOW:
            bucket[0], bucket[1] = now, 0.0
        bucket[1] += 1
        if bucket[1] > settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(status_code=429, content={"detail": t("rate_limit.exceeded")})
        return await call_next(request)
