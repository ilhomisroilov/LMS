"""Persisted refresh tokens with rotation + family revocation (v1.2 spec §12.1).

We store only a SHA-256 *hash* of the token (never the raw value). Tokens are
grouped by ``family_id``; rotating a token marks the old one replaced. If an
already-replaced/revoked token is presented (replay/theft), the whole family is
revoked.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # SHA-256 hex digest of the raw refresh JWT.
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    family_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[int | None] = mapped_column(Integer)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")  # noqa: F821
