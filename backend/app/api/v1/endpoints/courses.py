"""Course & LMS lesson endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.authz import AuthContext, require_permission
from app.core.deps import CurrentUser, DbSession, Language
from app.core.i18n import t
from app.core.permissions import Perm
from app.repositories.student_repository import StudentRepository
from app.schemas.common import Page
from app.schemas.course import (
    CourseCreate, CourseOut, CourseUpdate, LessonCreate, LessonOut, LessonUpdate, ProgressUpdate,
)
from app.services.course_service import CourseService
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/courses", tags=["courses", "lms"])
CanWrite = Depends(require_permission(Perm.COURSE_WRITE))


@router.get("", response_model=Page[CourseOut])
def list_courses(db: DbSession, user: CurrentUser, page: int = 1, size: int = 50):
    items, total = CourseService(db, user.organization_id).list_courses(page=page, size=size)
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=CourseOut, status_code=201)
def create_course(data: CourseCreate, db: DbSession, ctx: AuthContext = CanWrite):
    return CourseService(db, ctx.organization_id).create_course(data)


@router.patch("/{course_id}", response_model=CourseOut)
def update_course(course_id: int, data: CourseUpdate, db: DbSession, lang: Language,
                  ctx: AuthContext = CanWrite):
    try:
        return CourseService(db, ctx.organization_id).update_course(course_id, data)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.delete("/{course_id}", status_code=204)
def delete_course(course_id: int, db: DbSession, lang: Language, ctx: AuthContext = CanWrite):
    try:
        CourseService(db, ctx.organization_id).delete_course(course_id)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.get("/{course_id}/lessons", response_model=list[LessonOut])
def list_lessons(course_id: int, db: DbSession, user: CurrentUser):
    """Lessons for a course; includes per-student completion flag for students."""
    student_id = None
    if user.role.name == "student":
        student = StudentRepository(db).get_by_user_id(user.id)
        student_id = student.id if student else None
    return CourseService(db, user.organization_id).list_lessons(course_id, student_id)


@router.post("/lessons", response_model=LessonOut, status_code=201)
def create_lesson(data: LessonCreate, db: DbSession, lang: Language, ctx: AuthContext = CanWrite):
    try:
        return CourseService(db, ctx.organization_id).create_lesson(data)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.patch("/lessons/{lesson_id}", response_model=LessonOut)
def update_lesson(lesson_id: int, data: LessonUpdate, db: DbSession, lang: Language,
                  ctx: AuthContext = CanWrite):
    try:
        return CourseService(db, ctx.organization_id).update_lesson(lesson_id, data)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.delete("/lessons/{lesson_id}", status_code=204)
def delete_lesson(lesson_id: int, db: DbSession, lang: Language, ctx: AuthContext = CanWrite):
    try:
        CourseService(db, ctx.organization_id).delete_lesson(lesson_id)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.post("/lessons/{lesson_id}/progress", response_model=LessonOut)
def mark_progress(lesson_id: int, data: ProgressUpdate, db: DbSession, user: CurrentUser, lang: Language):
    student = StudentRepository(db).get_by_user_id(user.id)
    if not student:
        raise HTTPException(403, t("auth.forbidden", lang))
    try:
        return CourseService(db, user.organization_id).mark_progress(lesson_id, student.id, data.completed)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))
