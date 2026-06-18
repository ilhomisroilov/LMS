from __future__ import annotations
"""Course & LMS lesson management with progress tracking."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson, LessonProgress
from app.repositories.course_repository import CourseRepository, LessonRepository
from app.schemas.course import (
    CourseCreate, CourseOut, CourseUpdate, LessonCreate, LessonOut, LessonUpdate,
)
from app.services.exceptions import NotFoundError


class CourseService:
    def __init__(self, db: Session, organization_id: int | None = None) -> None:
        self.db = db
        self.organization_id = organization_id
        self.courses = CourseRepository(db)
        self.lessons = LessonRepository(db)

    # ---- Courses ----
    def _course_out(self, c: Course) -> CourseOut:
        return CourseOut(id=c.id, name=c.name, description=c.description,
                         lesson_count=self.courses.lesson_count(c.id))

    def list_courses(self, *, page=1, size=50):
        skip = (page - 1) * size
        rows = self.courses.list_for_org(skip=skip, limit=size, org_id=self.organization_id)
        return [self._course_out(c) for c in rows], self.courses.count_for_org(self.organization_id)

    def create_course(self, data: CourseCreate) -> CourseOut:
        c = Course(**data.model_dump(), organization_id=self.organization_id)
        self.courses.add(c)
        self.db.commit()
        return self._course_out(c)

    def update_course(self, course_id: int, data: CourseUpdate) -> CourseOut:
        c = self.courses.get_for_org(course_id, self.organization_id)
        if not c:
            raise NotFoundError()
        for f, v in data.model_dump(exclude_unset=True).items():
            setattr(c, f, v)
        self.db.commit()
        return self._course_out(c)

    def delete_course(self, course_id: int) -> None:
        c = self.courses.get_for_org(course_id, self.organization_id)
        if not c:
            raise NotFoundError()
        self.db.delete(c)
        self.db.commit()

    # ---- Lessons ----
    @staticmethod
    def _lesson_out(lsn: Lesson, completed: bool | None = None) -> LessonOut:
        return LessonOut(
            id=lsn.id, course_id=lsn.course_id, title=lsn.title,
            content_type=lsn.content_type, content=lsn.content, file_key=lsn.file_key,
            order_index=lsn.order_index, created_at=lsn.created_at, completed=completed,
        )

    def list_lessons(self, course_id: int, student_id: int | None = None) -> list[LessonOut]:
        if not self.courses.get_for_org(course_id, self.organization_id):
            raise NotFoundError()
        rows = self.lessons.by_course(course_id)
        progress = self.lessons.progress_for(student_id, [r.id for r in rows]) if student_id else {}
        return [self._lesson_out(r, progress.get(r.id) if student_id else None) for r in rows]

    def create_lesson(self, data: LessonCreate) -> LessonOut:
        if not self.courses.get_for_org(data.course_id, self.organization_id):
            raise NotFoundError()
        lsn = Lesson(**data.model_dump())
        self.lessons.add(lsn)
        self.db.commit()
        return self._lesson_out(lsn)

    def update_lesson(self, lesson_id: int, data: LessonUpdate) -> LessonOut:
        lsn = self.lessons.get_for_org(lesson_id, self.organization_id)
        if not lsn:
            raise NotFoundError()
        for f, v in data.model_dump(exclude_unset=True).items():
            setattr(lsn, f, v)
        self.db.commit()
        return self._lesson_out(lsn)

    def delete_lesson(self, lesson_id: int) -> None:
        lsn = self.lessons.get_for_org(lesson_id, self.organization_id)
        if not lsn:
            raise NotFoundError()
        self.db.delete(lsn)
        self.db.commit()

    def mark_progress(self, lesson_id: int, student_id: int, completed: bool) -> LessonOut:
        lsn = self.lessons.get_for_org(lesson_id, self.organization_id)
        if not lsn:
            raise NotFoundError()
        prog = self.lessons.get_progress(lesson_id, student_id)
        if not prog:
            prog = LessonProgress(lesson_id=lesson_id, student_id=student_id)
            self.db.add(prog)
        prog.completed = completed
        prog.completed_at = datetime.now(timezone.utc) if completed else None
        self.db.commit()
        return self._lesson_out(lsn, completed)
