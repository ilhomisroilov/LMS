"""Audit-log writer (v1.2 spec §14.2).

Sensitive actions call ``write_audit(...)`` which appends an immutable row.
Writing is best-effort and must never break the primary action: failures are
logged, not raised. (In production this would run via the event bus / worker;
here it writes synchronously in the same session.)
"""
from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger("educore.audit")


def _enc(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return json.dumps(value, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def write_audit(
    db: Session,
    *,
    action: str,
    organization_id: int | None = None,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    entity_type: str | None = None,
    entity_id: Any = None,
    before: Any = None,
    after: Any = None,
    ip: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
    commit: bool = False,
) -> None:
    """Append one audit row. Set ``commit=True`` to flush+commit immediately."""
    try:
        row = AuditLog(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=None if entity_id is None else str(entity_id),
            before=_enc(before),
            after=_enc(after),
            ip=ip,
            user_agent=user_agent,
            request_id=request_id,
        )
        db.add(row)
        if commit:
            db.commit()
        else:
            db.flush()
    except Exception:  # pragma: no cover - audit must not break the action
        logger.exception("Failed to write audit log for action=%s", action)
        db.rollback()
