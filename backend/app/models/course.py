"""Course = subject/curriculum that groups follow and lessons belong to."""
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    groups: Mapped[list["Group"]] = relationship(back_populates="course")  # noqa: F821
    lessons: Mapped[list["Lesson"]] = relationship(  # noqa: F821
        back_populates="course", cascade="all, delete-orphan", order_by="Lesson.order_index"
    )
