"""Student profile (1:1 with User)."""
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StudentStatus


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    parent_phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[StudentStatus] = mapped_column(
        Enum(StudentStatus), default=StudentStatus.active, nullable=False, index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("parents.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="student")  # noqa: F821
    parent: Mapped["Parent | None"] = relationship(back_populates="children")  # noqa: F821
    group_links: Mapped[list["GroupStudent"]] = relationship(  # noqa: F821
        back_populates="student", cascade="all, delete-orphan"
    )
    attendance: Mapped[list["Attendance"]] = relationship(
        back_populates="student", cascade="all, delete-orphan")  # noqa: F821
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan")  # noqa: F821
    lesson_progress: Mapped[list["LessonProgress"]] = relationship(
        back_populates="student", cascade="all, delete-orphan")  # noqa: F821
