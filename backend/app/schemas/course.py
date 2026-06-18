"""Course & lesson schemas."""
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import LessonContentType
from app.schemas.common import ORMModel


class CourseBase(BaseModel):
    name: str
    description: str | None = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CourseOut(ORMModel):
    id: int
    name: str
    description: str | None
    lesson_count: int = 0


class LessonBase(BaseModel):
    course_id: int
    title: str
    content_type: LessonContentType = LessonContentType.text
    content: str | None = None
    order_index: int = 0


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    title: str | None = None
    content_type: LessonContentType | None = None
    content: str | None = None
    order_index: int | None = None


class LessonOut(ORMModel):
    id: int
    course_id: int
    title: str
    content_type: LessonContentType
    content: str | None
    file_key: str | None
    order_index: int
    created_at: datetime
    completed: bool | None = None  # per requesting student, when relevant


class ProgressUpdate(BaseModel):
    completed: bool = True
