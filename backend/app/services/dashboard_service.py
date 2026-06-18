from __future__ import annotations
"""Admin dashboard aggregate stats (efficient COUNT/SUM, short-lived cache)."""
import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enums import StudentStatus
from app.models.group import Group
from app.models.student import Student
from app.models.teacher import Teacher
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import DashboardStats

# Process-wide cache: dashboard numbers change slowly, and the panel may be
# opened/refocused frequently. Cache must be keyed by organization to avoid
# leaking another tenant's aggregates into the current dashboard.
_CACHE_TTL = 20.0
_cache: dict[int, dict[str, object]] = {}


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.payments = PaymentRepository(db)
        self.attendance = AttendanceRepository(db)

    def _count(self, model, *where) -> int:
        stmt = select(func.count()).select_from(model)
        for w in where:
            stmt = stmt.where(w)
        return self.db.scalar(stmt) or 0

    def stats(self, organization_id: int | None = None) -> DashboardStats:
        now = time.time()
        cache_key = organization_id or 0
        entry = _cache.get(cache_key, {"ts": 0.0, "data": None})
        cached = entry["data"]
        if cached is not None and (now - float(entry["ts"])) < _CACHE_TTL:
            return cached  # type: ignore[return-value]

        month = self.payments.current_month()
        where = ()
        if organization_id is not None:
            where = (Student.organization_id == organization_id,)
        teacher_where = (Teacher.organization_id == organization_id,) if organization_id is not None else ()
        group_where = (Group.organization_id == organization_id,) if organization_id is not None else ()
        course_where = (Course.organization_id == organization_id,) if organization_id is not None else ()
        data = DashboardStats(
            total_students=self._count(Student, *where),
            active_students=self._count(Student, Student.status == StudentStatus.active, *where),
            total_teachers=self._count(Teacher, *teacher_where),
            active_groups=self._count(Group, *group_where),
            total_courses=self._count(Course, *course_where),
            revenue_this_month=self.payments.revenue_for_month(month, organization_id),
            debt_total=self.payments.total_debt(organization_id),
            attendance_rate=self.attendance.attendance_rate(30, organization_id),
        )
        _cache[cache_key] = {"ts": now, "data": data}
        return data

    @staticmethod
    def invalidate() -> None:
        _cache.clear()
