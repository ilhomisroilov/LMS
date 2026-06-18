"""Student schemas."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import StudentStatus
from app.schemas.common import ORMModel


class StudentBase(BaseModel):
    full_name: str
    phone: str
    parent_phone: str | None = None
    status: StudentStatus = StudentStatus.active
    language: str = "uz"


class StudentCreate(StudentBase):
    password: str = Field("student123", min_length=6)
    group_id: int | None = None
    parent_id: int | None = None


class StudentUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    parent_phone: str | None = None
    status: StudentStatus | None = None
    parent_id: int | None = None
    language: str | None = None


class StudentOut(ORMModel):
    id: int
    user_id: int
    full_name: str
    phone: str
    parent_phone: str | None
    status: StudentStatus
    parent_id: int | None
    created_at: datetime
    group_ids: list[int] = []
