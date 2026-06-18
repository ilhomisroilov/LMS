"""Attendance schemas."""
from datetime import date

from pydantic import BaseModel

from app.models.enums import AttendanceStatus
from app.schemas.common import ORMModel


class AttendanceItem(BaseModel):
    student_id: int
    status: AttendanceStatus = AttendanceStatus.present


class AttendanceBulkCreate(BaseModel):
    group_id: int
    lesson_date: date
    records: list[AttendanceItem]


class AttendanceOut(ORMModel):
    id: int
    student_id: int
    group_id: int
    lesson_date: date
    status: AttendanceStatus
    student_name: str | None = None
