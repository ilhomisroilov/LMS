"""Teacher profile (1:1 with User)."""
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    salary: Mapped[float | None] = mapped_column(Numeric(12, 2))
    subjects: Mapped[str | None] = mapped_column(String(255))  # comma-separated for V1

    user: Mapped["User"] = relationship(back_populates="teacher")  # noqa: F821
    groups: Mapped[list["Group"]] = relationship(back_populates="teacher")  # noqa: F821
