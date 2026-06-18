from __future__ import annotations
"""Self-service aggregation for the logged-in user (frontend /me & Telegram bot)."""
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.group_repository import GroupRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_repository import TeacherRepository
from app.schemas.attendance import AttendanceOut
from app.schemas.course import LessonOut
from app.schemas.group import GroupOut
from app.schemas.payment import PaymentOut
from app.schemas.student import StudentOut
from app.services.attendance_service import AttendanceService
from app.services.course_service import CourseService
from app.services.exceptions import NotFoundError
from app.services.group_service import GroupService
from app.services.payment_service import PaymentService


class SelfService:
    """Maps a User -> their student/teacher/parent data without leaking other users'."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.students = StudentRepository(db)
        self.teachers = TeacherRepository(db)
        self.groups = GroupRepository(db)

    # ---------- Student ----------
    def _student(self, user: User):
        s = self.students.get_by_user_id(user.id)
        if not s:
            raise NotFoundError()
        return s

    def student_groups(self, user: User) -> list[GroupOut]:
        s = self._student(user)
        gsvc = GroupService(self.db, user.organization_id)
        return [gsvc.get(gid) for gid in self.students.group_ids(s.id)]

    def student_attendance(self, user: User) -> list[AttendanceOut]:
        return AttendanceService(self.db, user.organization_id).student_history(self._student(user).id)

    def student_payments(self, user: User) -> list[PaymentOut]:
        return PaymentService(self.db, user.organization_id).student_history(self._student(user).id)

    def student_lessons(self, user: User) -> list[LessonOut]:
        s = self._student(user)
        csvc = CourseService(self.db, user.organization_id)
        out: list[LessonOut] = []
        for gid in self.students.group_ids(s.id):
            g = self.groups.get(gid)
            if g and g.course_id:
                out.extend(csvc.list_lessons(g.course_id, s.id))
        return out

    # ---------- Teacher ----------
    def teacher_groups(self, user: User) -> list[GroupOut]:
        t = self.teachers.get_by_user_id(user.id)
        if not t:
            raise NotFoundError()
        gsvc = GroupService(self.db, user.organization_id)
        return [gsvc.get(g.id) for g in self.groups.groups_for_teacher(t.id, user.organization_id)]

    # ---------- Parent ----------
    def parent_children(self, user: User):
        from app.services.student_service import StudentService

        parent = self._parent(user)
        svc = StudentService(self.db, user.organization_id)
        return [svc.get(c.id) for c in parent.children]

    def parent_child_attendance(self, user: User, student_id: int) -> list[AttendanceOut]:
        child = self._parent_child(user, student_id)
        return AttendanceService(self.db, user.organization_id).student_history(child.id)

    def parent_child_payments(self, user: User, student_id: int) -> list[PaymentOut]:
        child = self._parent_child(user, student_id)
        return PaymentService(self.db, user.organization_id).student_history(child.id)

    def parent_child_lessons(self, user: User, student_id: int) -> list[LessonOut]:
        child = self._parent_child(user, student_id)
        csvc = CourseService(self.db, user.organization_id)
        out: list[LessonOut] = []
        for gid in self.students.group_ids(child.id):
            group = self.groups.get(gid)
            if group and group.organization_id == user.organization_id and group.course_id:
                out.extend(csvc.list_lessons(group.course_id, child.id))
        return out

    def _parent(self, user: User):
        parent = user.parent
        if not parent or parent.organization_id != user.organization_id:
            raise NotFoundError()
        return parent

    def _parent_child(self, user: User, student_id: int):
        parent = self._parent(user)
        child = next(
            (
                item
                for item in parent.children
                if item.id == student_id and item.organization_id == user.organization_id
            ),
            None,
        )
        if not child:
            raise NotFoundError()
        return child
