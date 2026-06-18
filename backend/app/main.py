"""EduCore CRM + LMS — FastAPI application entrypoint."""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import logs
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.rate_limit import RateLimitMiddleware
from app.core.timing import TimingMiddleware

logging.basicConfig(level=logging.INFO)
logging.getLogger("educore.timing").setLevel(logging.INFO)

app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
)

# Order matters: TimingMiddleware is added last so it sits OUTERMOST and
# measures the full request (including the rate-limit check).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TimingMiddleware)

register_exception_handlers(app)

# Serve locally stored files (V1 storage backend)
Path(settings.STORAGE_LOCAL_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=settings.STORAGE_LOCAL_DIR), name="uploads")

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
# Also expose logs under /api/logs for compatibility with clients that omit /v1.
app.include_router(logs.router, prefix="/api")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.PROJECT_NAME}
