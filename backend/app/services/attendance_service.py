from __future__ import annotations
"""Attendance marking & history."""
from datetime import date

from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.group import Group
from app.models.student import Student
from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.attendance import AttendanceBulkCreate, AttendanceOut
from app.services.exceptions import NotFoundError


class AttendanceService:
    def __init__(self, db: Session, org_id: int | None = None) -> None:
        self.db = db
        self.org_id = org_id
        self.repo = AttendanceRepository(db)

    @staticmethod
    def _to_out(a: Attendance) -> AttendanceOut:
        return AttendanceOut(
            id=a.id, student_id=a.student_id, group_id=a.group_id,
            lesson_date=a.lesson_date, status=a.status,
            student_name=a.student.user.full_name if a.student and a.student.user else None,
        )

    def mark_bulk(self, data: AttendanceBulkCreate) -> list[AttendanceOut]:
        """Upsert attendance for a whole group on a given date."""
        self._ensure_group(data.group_id)
        out: list[Attendance] = []
        for rec in data.records:
            self._ensure_student(rec.student_id)
            existing = self.repo.get_day(rec.student_id, data.group_id, data.lesson_date)
            if existing:
                existing.status = rec.status
                out.append(existing)
            else:
                a = Attendance(
                    student_id=rec.student_id, group_id=data.group_id,
                    organization_id=self.org_id,
                    lesson_date=data.lesson_date, status=rec.status,
                )
                self.repo.add(a)
                out.append(a)
        self.db.commit()
        return [self.get(a.id) for a in out]

    def get(self, attendance_id: int) -> AttendanceOut:
        a = self.repo.get(attendance_id)
        if not a or (self.org_id is not None and a.organization_id != self.org_id):
            raise NotFoundError()
        return self._to_out(a)

    def group_history(self, group_id: int, lesson_date: date | None = None) -> list[AttendanceOut]:
        self._ensure_group(group_id)
        return [self._to_out(a) for a in self.repo.for_group(group_id, lesson_date, self.org_id)]

    def student_history(self, student_id: int) -> list[AttendanceOut]:
        return [self._to_out(a) for a in self.repo.for_student(student_id, self.org_id)]

    def _ensure_group(self, group_id: int) -> None:
        group = self.db.get(Group, group_id)
        if not group or (self.org_id is not None and group.organization_id != self.org_id):
            raise NotFoundError()

    def _ensure_student(self, student_id: int) -> None:
        student = self.db.get(Student, student_id)
        if not student or (self.org_id is not None and student.organization_id != self.org_id):
            raise NotFoundError()
