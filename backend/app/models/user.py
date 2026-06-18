"""Core authentication user. Profile rows (student/teacher/parent) link 1:1."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserStatus(str, __import__("enum").Enum):
    invited = "invited"        # created, no usable password yet
    active = "active"
    suspended = "suspended"
    disabled = "disabled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ---- Tenancy (v1.2) ----
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[int | None] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True
    )

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    # Nullable: an invited user has no password until they accept the invite.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Bumped to force-logout-all sessions; embedded in access tokens as ``tv``.
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    language: Mapped[str] = mapped_column(String(2), default="uz", nullable=False)
    telegram_id: Mapped[int | None] = mapped_column(unique=True, index=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    role: Mapped["Role"] = relationship(back_populates="users")  # noqa: F821

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped["Student | None"] = relationship(
        back_populates="user", uselist=False,
        cascade="all, delete-orphan")  # noqa: F821
    teacher: Mapped["Teacher | None"] = relationship(
        back_populates="user", uselist=False,
        cascade="all, delete-orphan")  # noqa: F821
    parent: Mapped["Parent | None"] = relationship(
        back_populates="user", uselist=False,
        cascade="all, delete-orphan")  # noqa: F821
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
