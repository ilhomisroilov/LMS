"""Group / course-cohort schemas."""
from pydantic import BaseModel

from app.schemas.common import ORMModel


class GroupBase(BaseModel):
    name: str
    course_id: int | None = None
    teacher_id: int | None = None
    schedule_days: str | None = None
    schedule_time: str | None = None


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: str | None = None
    course_id: int | None = None
    teacher_id: int | None = None
    schedule_days: str | None = None
    schedule_time: str | None = None


class GroupOut(ORMModel):
    id: int
    name: str
    course_id: int | None
    teacher_id: int | None
    teacher_name: str | None = None
    course_name: str | None = None
    schedule_days: str | None
    schedule_time: str | None
    student_count: int = 0


class AssignStudents(BaseModel):
    student_ids: list[int]
