"""Self-service endpoints for the authenticated user (used by frontend & bot login)."""
from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, DbSession, Language
from app.core.i18n import t
from app.schemas.attendance import AttendanceOut
from app.schemas.course import LessonOut
from app.schemas.group import GroupOut
from app.schemas.payment import PaymentOut
from app.schemas.student import StudentOut
from app.services.exceptions import ServiceError
from app.services.self_service import SelfService

router = APIRouter(prefix="/me", tags=["me"])


def _guard(fn, lang):
    try:
        return fn()
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.get("/groups", response_model=list[GroupOut])
def my_groups(db: DbSession, user: CurrentUser, lang: Language):
    svc = SelfService(db)
    if user.role.name == "teacher":
        return _guard(lambda: svc.teacher_groups(user), lang)
    return _guard(lambda: svc.student_groups(user), lang)


@router.get("/attendance", response_model=list[AttendanceOut])
def my_attendance(db: DbSession, user: CurrentUser, lang: Language):
    return _guard(lambda: SelfService(db).student_attendance(user), lang)


@router.get("/payments", response_model=list[PaymentOut])
def my_payments(db: DbSession, user: CurrentUser, lang: Language):
    return _guard(lambda: SelfService(db).student_payments(user), lang)


@router.get("/lessons", response_model=list[LessonOut])
def my_lessons(db: DbSession, user: CurrentUser, lang: Language):
    return _guard(lambda: SelfService(db).student_lessons(user), lang)


@router.get("/children", response_model=list[StudentOut])
def my_children(db: DbSession, user: CurrentUser, lang: Language):
    return _guard(lambda: SelfService(db).parent_children(user), lang)


@router.get("/children/{student_id}/attendance", response_model=list[AttendanceOut])
def child_attendance(student_id: int, db: DbSession, user: CurrentUser, lang: Language):
    return _guard(
        lambda: SelfService(db).parent_child_attendance(user, student_id), lang
    )


@router.get("/children/{student_id}/payments", response_model=list[PaymentOut])
def child_payments(student_id: int, db: DbSession, user: CurrentUser, lang: Language):
    return _guard(
        lambda: SelfService(db).parent_child_payments(user, student_id), lang
    )


@router.get("/children/{student_id}/lessons", response_model=list[LessonOut])
def child_lessons(student_id: int, db: DbSession, user: CurrentUser, lang: Language):
    return _guard(
        lambda: SelfService(db).parent_child_lessons(user, student_id), lang
    )
