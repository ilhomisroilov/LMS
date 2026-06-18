"""Course & lesson data access."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson, LessonProgress
from app.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, db: Session) -> None:
        super().__init__(Course, db)

    def get_for_org(self, course_id: int, org_id: int | None = None) -> Course | None:
        stmt = select(Course).where(Course.id == course_id)
        if org_id is not None:
            stmt = stmt.where(Course.organization_id == org_id)
        return self.db.scalar(stmt)

    def list_for_org(self, *, skip: int = 0, limit: int = 50,
                     org_id: int | None = None) -> list[Course]:
        stmt = select(Course).order_by(Course.id).offset(skip).limit(limit)
        if org_id is not None:
            stmt = stmt.where(Course.organization_id == org_id)
        return list(self.db.scalars(stmt).all())

    def count_for_org(self, org_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Course)
        if org_id is not None:
            stmt = stmt.where(Course.organization_id == org_id)
        return self.db.scalar(stmt) or 0

    def lesson_count(self, course_id: int) -> int:
        return self.db.scalar(
            select(func.count()).select_from(Lesson).where(Lesson.course_id == course_id)
        ) or 0


class LessonRepository(BaseRepository[Lesson]):
    def __init__(self, db: Session) -> None:
        super().__init__(Lesson, db)

    def by_course(self, course_id: int) -> list[Lesson]:
        return list(
            self.db.scalars(
                select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.order_index)
            ).all()
        )

    def get_for_org(self, lesson_id: int, org_id: int | None = None) -> Lesson | None:
        stmt = select(Lesson).join(Course, Course.id == Lesson.course_id).where(Lesson.id == lesson_id)
        if org_id is not None:
            stmt = stmt.where(Course.organization_id == org_id)
        return self.db.scalar(stmt)

    def progress_for(self, student_id: int, lesson_ids: list[int]) -> dict[int, bool]:
        if not lesson_ids:
            return {}
        rows = self.db.execute(
            select(LessonProgress.lesson_id, LessonProgress.completed).where(
                LessonProgress.student_id == student_id,
                LessonProgress.lesson_id.in_(lesson_ids),
            )
        ).all()
        return {lid: done for lid, done in rows}

    def get_progress(self, lesson_id: int, student_id: int) -> LessonProgress | None:
        return self.db.scalar(
            select(LessonProgress).where(
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.student_id == student_id,
            )
        )
