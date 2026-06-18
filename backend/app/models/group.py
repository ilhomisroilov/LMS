"""Group (a class cohort) + group_students association."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), index=True
    )
    teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"), index=True
    )
    schedule_days: Mapped[str | None] = mapped_column(String(60))
    schedule_time: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course: Mapped["Course | None"] = relationship(back_populates="groups")  # noqa: F821
    teacher: Mapped["Teacher | None"] = relationship(back_populates="groups")  # noqa: F821
    student_links: Mapped[list["GroupStudent"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    attendance: Mapped[list["Attendance"]] = relationship(back_populates="group")  # noqa: F821


class GroupStudent(Base):
    """Many-to-many association between groups and students."""

    __tablename__ = "group_students"
    __table_args__ = (UniqueConstraint("group_id", "student_id", name="uq_group_student"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped["Group"] = relationship(back_populates="student_links")
    student: Mapped["Student"] = relationship(back_populates="group_links")  # noqa: F821
