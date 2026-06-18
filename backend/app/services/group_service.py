from __future__ import annotations
"""Group / cohort management."""
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.group import Group, GroupStudent
from app.models.student import Student
from app.models.teacher import Teacher
from app.repositories.group_repository import GroupRepository
from app.schemas.group import GroupCreate, GroupOut, GroupUpdate
from app.schemas.student import StudentOut
from app.services.exceptions import NotFoundError
from app.services.student_service import StudentService


class GroupService:
    def __init__(self, db: Session, org_id: int | None = None) -> None:
        self.db = db
        self.org_id = org_id
        self.repo = GroupRepository(db)

    def _to_out(self, g: Group) -> GroupOut:
        return GroupOut(
            id=g.id, name=g.name, course_id=g.course_id, teacher_id=g.teacher_id,
            teacher_name=g.teacher.user.full_name if g.teacher else None,
            course_name=g.course.name if g.course else None,
            schedule_days=g.schedule_days, schedule_time=g.schedule_time,
            student_count=self.repo.student_count(g.id),
        )

    def list(self, *, page=1, size=50):
        skip = (page - 1) * size
        rows = self.repo.list_full(skip=skip, limit=size, org_id=self.org_id)
        return [self._to_out(g) for g in rows], self.repo.count_for_org(self.org_id)

    def get(self, group_id: int) -> GroupOut:
        g = self.repo.get_full(group_id, self.org_id)
        if not g:
            raise NotFoundError()
        return self._to_out(g)

    def create(self, data: GroupCreate) -> GroupOut:
        self._validate_links(data.course_id, data.teacher_id)
        g = Group(**data.model_dump(), organization_id=self.org_id)
        self.repo.add(g)
        self.db.commit()
        return self.get(g.id)

    def update(self, group_id: int, data: GroupUpdate) -> GroupOut:
        g = self.repo.get_full(group_id, self.org_id)
        if not g:
            raise NotFoundError()
        self._validate_links(data.course_id, data.teacher_id)
        for field, val in data.model_dump(exclude_unset=True).items():
            setattr(g, field, val)
        self.db.commit()
        return self.get(group_id)

    def delete(self, group_id: int) -> None:
        g = self.repo.get_full(group_id, self.org_id)
        if not g:
            raise NotFoundError()
        self.db.delete(g)
        self.db.commit()

    def assign_students(self, group_id: int, student_ids: list[int]) -> GroupOut:
        if not self.repo.get_full(group_id, self.org_id):
            raise NotFoundError()
        for sid in student_ids:
            student = self.db.get(Student, sid)
            if not student or student.organization_id != self.org_id:
                raise NotFoundError()
            if not self.repo.link_exists(group_id, sid):
                self.db.add(GroupStudent(group_id=group_id, student_id=sid))
        self.db.commit()
        return self.get(group_id)

    def remove_student(self, group_id: int, student_id: int) -> None:
        link = next(
            (gl for gl in self.repo.get_full(group_id, self.org_id).student_links if gl.student_id == student_id),
            None,
        ) if self.repo.get_full(group_id, self.org_id) else None
        if link:
            self.db.delete(link)
            self.db.commit()

    def students(self, group_id: int) -> list[StudentOut]:
        if not self.repo.get_full(group_id, self.org_id):
            raise NotFoundError()
        svc = StudentService(self.db, self.org_id)
        return [svc._to_out(s) for s in self.repo.students(group_id, self.org_id)]

    def _validate_links(self, course_id: int | None, teacher_id: int | None) -> None:
        if self.org_id is None:
            raise NotFoundError()
        if course_id:
            course = self.db.get(Course, course_id)
            if not course or course.organization_id != self.org_id:
                raise NotFoundError()
        if teacher_id:
            teacher = self.db.get(Teacher, teacher_id)
            if not teacher or teacher.organization_id != self.org_id:
                raise NotFoundError()
