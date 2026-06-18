"""Centralized exception handlers — clean JSON instead of raw 500 tracebacks."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.i18n import t
from app.services.exceptions import ServiceError

logger = logging.getLogger("educore.errors")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceError)
    async def _service_error(request: Request, exc: ServiceError):
        lang = request.headers.get("accept-language", "").split(",")[0].split("-")[0]
        return JSONResponse(status_code=exc.status_code, content={"detail": t(exc.msg_key, lang)})

    @app.exception_handler(IntegrityError)
    async def _integrity_error(request: Request, exc: IntegrityError):
        # Expected constraint violation (e.g. duplicate phone) -> 409, not 500.
        lang = request.headers.get("accept-language", "").split(",")[0].split("-")[0]
        logger.info("IntegrityError on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=409, content={"detail": t("common.already_exists", lang)})
