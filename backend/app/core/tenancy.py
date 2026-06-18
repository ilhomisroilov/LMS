"""Multi-tenant foundation (v1.2).

Every business table carries ``organization_id`` (and an optional
``branch_id``) so that tenant isolation is structural, not incidental. The
mixins here are mixed into ORM models; the request-scoped helpers expose the
current tenant derived from the authenticated user.

Design rule (spec §7.2): the repository layer ALWAYS filters by
``organization_id`` taken from the AuthContext. A query that forgets the tenant
filter is a code smell that should fail review.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """created_at / updated_at on every row."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    """Soft-delete marker. Repositories filter ``deleted_at IS NULL`` by default."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class TenantMixin:
    """organization_id (+ optional branch_id) on every scoped table.

    ``branch_id`` NULL means org-wide. We keep ``organization_id`` indexed and
    expect composite indexes (org_id, <filter>) on concrete tables.
    """

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    branch_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True
    )


class TenantScopedMixin(TenantMixin, TimestampMixin, SoftDeleteMixin):
    """Convenience: tenant + timestamps + soft delete in one mixin."""
