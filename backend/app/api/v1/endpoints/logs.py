from __future__ import annotations

"""Lightweight log status endpoints for the admin UI.

Mounted at both /api/v1/logs and /api/logs (compatibility). All endpoints are
cheap and non-blocking. The SSE stream emits a heartbeat every 15s and is
excluded from rate-limit/timing middleware so it never holds up the server.
"""

import asyncio
import collections
import json
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/logs", tags=["logs"])
_STARTED_AT = time.time()

# Small in-memory ring buffer of recent log lines (no DB, no disk).
_RECENT: collections.deque[dict] = collections.deque(maxlen=200)


class _BufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            _RECENT.append({
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            })
        except Exception:
            pass


# Attach once to the timing/errors loggers so /recent has useful content.
_handler = _BufferHandler()
for _name in ("educore.timing", "educore.errors"):
    logging.getLogger(_name).addHandler(_handler)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/stats")
def logs_stats() -> dict[str, object]:
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - _STARTED_AT),
        "recent_count": len(_RECENT),
        "stream": "/api/v1/logs/stream",
        "last_event_at": _now(),
    }


@router.get("/recent")
def logs_recent(limit: int = 100) -> dict[str, object]:
    limit = max(1, min(limit, 200))
    items = list(_RECENT)[-limit:]
    return {"items": items, "count": len(items)}


async def _events(once: bool = False):
    yield "retry: 10000\n\n"
    while True:
        payload = {"type": "heartbeat", "message": "EduCore backend is running",
                   "timestamp": _now()}
        yield f"event: heartbeat\ndata: {json.dumps(payload)}\n\n"
        if once:
            return
        await asyncio.sleep(15)


@router.get("/stream")
async def logs_stream(once: bool = False) -> StreamingResponse:
    return StreamingResponse(
        _events(once=once),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                 "Connection": "keep-alive"},
    )
