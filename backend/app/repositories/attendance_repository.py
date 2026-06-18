"""Attendance data access."""
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance
from app.models.enums import AttendanceStatus
from app.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):
    def __init__(self, db: Session) -> None:
        super().__init__(Attendance, db)

    def get_day(self, student_id: int, group_id: int, lesson_date: date) -> Attendance | None:
        return self.db.scalar(
            select(Attendance).where(
                Attendance.student_id == student_id,
                Attendance.group_id == group_id,
                Attendance.lesson_date == lesson_date,
            )
        )

    def for_group(self, group_id: int, lesson_date: date | None = None,
                  org_id: int | None = None) -> list[Attendance]:
        stmt = select(Attendance).options(
            joinedload(Attendance.student)
        ).where(Attendance.group_id == group_id)
        if org_id is not None:
            stmt = stmt.where(Attendance.organization_id == org_id)
        if lesson_date:
            stmt = stmt.where(Attendance.lesson_date == lesson_date)
        return list(self.db.scalars(stmt.order_by(Attendance.lesson_date.desc())).unique().all())

    def for_student(self, student_id: int, org_id: int | None = None) -> list[Attendance]:
        stmt = (
            select(Attendance)
            .where(Attendance.student_id == student_id)
            .order_by(Attendance.lesson_date.desc())
        )
        if org_id is not None:
            stmt = stmt.where(Attendance.organization_id == org_id)
        return list(self.db.scalars(stmt).all())

    def attendance_rate(self, days: int = 30, org_id: int | None = None) -> float:
        since = date.today() - timedelta(days=days)
        total_stmt = select(func.count()).select_from(Attendance).where(
            Attendance.lesson_date >= since
        )
        if org_id is not None:
            total_stmt = total_stmt.where(Attendance.organization_id == org_id)
        total = self.db.scalar(total_stmt) or 0
        if total == 0:
            return 0.0
        present_stmt = select(func.count()).select_from(Attendance).where(
            Attendance.lesson_date >= since,
            Attendance.status == AttendanceStatus.present,
        )
        if org_id is not None:
            present_stmt = present_stmt.where(Attendance.organization_id == org_id)
        present = self.db.scalar(present_stmt) or 0
        return round(present * 100 / total, 1)
