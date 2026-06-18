"""Teacher schemas."""
from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class TeacherBase(BaseModel):
    full_name: str
    phone: str
    salary: float | None = None
    subjects: str | None = None
    language: str = "uz"


class TeacherCreate(TeacherBase):
    password: str = Field("teacher123", min_length=6)


class TeacherUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    salary: float | None = None
    subjects: str | None = None


class TeacherOut(ORMModel):
    id: int
    user_id: int
    full_name: str
    phone: str
    salary: float | None
    subjects: str | None
