"""Request-timing middleware.

Pure ASGI (not BaseHTTPMiddleware) so it never buffers streaming/SSE responses.
Logs method, path, status and duration, tagging requests slower than 300ms / 1s / 3s.
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger("educore.timing")

_SKIP_SUFFIXES = ("/logs/stream",)


def _tag(ms: float) -> str:
    if ms >= 3000:
        return "VERY_SLOW>3s"
    if ms >= 1000:
        return "SLOW>1s"
    if ms >= 300:
        return "WARN>300ms"
    return "ok"


class TimingMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        if path.endswith(_SKIP_SUFFIXES):
            return await self.app(scope, receive, send)

        start = time.perf_counter()
        status_code = 0

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            ms = (time.perf_counter() - start) * 1000.0
            tag = _tag(ms)
            method = scope.get("method", "?")
            line = f"{method} {path} -> {status_code} {ms:.0f}ms [{tag}]"
            if ms >= 1000:
                logger.warning(line)
            elif ms >= 300:
                logger.info(line)
            else:
                logger.debug(line)
