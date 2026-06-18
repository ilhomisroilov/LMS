"""Internal API for the Telegram bot.

Secured by the X-Bot-Token shared secret. The bot authenticates end users by
phone number (Telegram 'share contact'), which links their telegram_id to a
User. Subsequent calls are resolved by telegram_id.
"""
from datetime import date

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import DbSession
from app.models.attendance import Attendance
from app.repositories.user_repository import UserRepository
from app.schemas.attendance import AttendanceBulkCreate, AttendanceOut
from app.schemas.course import LessonOut
from app.schemas.group import GroupOut
from app.schemas.payment import PaymentOut
from app.schemas.student import StudentOut
from app.services.attendance_service import AttendanceService
from app.services.exceptions import NotFoundError, ServiceError
from app.services.group_service import GroupService
from app.services.self_service import SelfService

router = APIRouter(prefix="/bot", tags=["bot"])


def _auth(token: str | None) -> None:
    if token != settings.BOT_API_TOKEN:
        raise HTTPException(401, "Invalid bot token")


def _user_by_tg(db, telegram_id: int):
    user = UserRepository(db).get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(404, "User not linked")
    return user


class LinkRequest(BaseModel):
    phone: str
    telegram_id: int


class BotUserOut(BaseModel):
    user_id: int
    full_name: str
    role: str
    language: str


class BotAttendanceMark(BaseModel):
    telegram_id: int
    group_id: int
    lesson_date: date
    records: list[dict]  # [{student_id, status}]


@router.post("/link", response_model=BotUserOut)
def link_account(data: LinkRequest, db: DbSession, x_bot_token: str | None = Header(default=None)):
    """Match a phone number to a user and bind the Telegram id."""
    _auth(x_bot_token)
    users = UserRepository(db)
    phone = data.phone if data.phone.startswith("+") else f"+{data.phone.lstrip('+')}"
    user = users.get_by_phone(phone) or users.get_by_phone(data.phone)
    if not user:
        raise HTTPException(404, "Phone not registered")
    user.telegram_id = data.telegram_id
    db.commit()
    return BotUserOut(user_id=user.id, full_name=user.full_name,
                      role=user.role.name, language=user.language)


@router.get("/me", response_model=BotUserOut)
def bot_me(telegram_id: int, db: DbSession, x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    user = _user_by_tg(db, telegram_id)
    return BotUserOut(user_id=user.id, full_name=user.full_name,
                      role=user.role.name, language=user.language)


@router.post("/language", response_model=BotUserOut)
def set_language(telegram_id: int, lang: str, db: DbSession,
                 x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    user = _user_by_tg(db, telegram_id)
    if lang in {"uz", "en"}:
        user.language = lang
        db.commit()
    return BotUserOut(user_id=user.id, full_name=user.full_name,
                      role=user.role.name, language=user.language)


def _guard(fn):
    try:
        return fn()
    except ServiceError:
        raise HTTPException(404, "Not found")


# ---- Student ----
@router.get("/student/groups", response_model=list[GroupOut])
def student_groups(telegram_id: int, db: DbSession, x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    return _guard(lambda: SelfService(db).student_groups(_user_by_tg(db, telegram_id)))


@router.get("/student/attendance", response_model=list[AttendanceOut])
def student_attendance(telegram_id: int, db: DbSession, x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    return _guard(lambda: SelfService(db).student_attendance(_user_by_tg(db, telegram_id)))


@router.get("/student/payments", response_model=list[PaymentOut])
def student_payments(telegram_id: int, db: DbSession, x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    return _guard(lambda: SelfService(db).student_payments(_user_by_tg(db, telegram_id)))


@router.get("/student/lessons", response_model=list[LessonOut])
def student_lessons(telegram_id: int, db: DbSession, x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    return _guard(lambda: SelfService(db).student_lessons(_user_by_tg(db, telegram_id)))


# ---- Teacher ----
@router.get("/teacher/groups", response_model=list[GroupOut])
def teacher_groups(telegram_id: int, db: DbSession, x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    return _guard(lambda: SelfService(db).teacher_groups(_user_by_tg(db, telegram_id)))


@router.get("/teacher/group/{group_id}/students", response_model=list[StudentOut])
def teacher_group_students(group_id: int, telegram_id: int, db: DbSession,
                           x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    user = _user_by_tg(db, telegram_id)
    return _guard(lambda: GroupService(db, user.organization_id).students(group_id))


@router.post("/teacher/attendance", response_model=list[AttendanceOut])
def teacher_mark_attendance(data: BotAttendanceMark, db: DbSession,
                            x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    user = _user_by_tg(db, data.telegram_id)
    payload = AttendanceBulkCreate(
        group_id=data.group_id, lesson_date=data.lesson_date, records=data.records
    )
    return AttendanceService(db, user.organization_id).mark_bulk(payload)


# ---- Parent ----
@router.get("/parent/children", response_model=list[StudentOut])
def parent_children(telegram_id: int, db: DbSession, x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    return _guard(lambda: SelfService(db).parent_children(_user_by_tg(db, telegram_id)))


@router.get("/parent/child/{student_id}/attendance", response_model=list[AttendanceOut])
def parent_child_attendance(student_id: int, telegram_id: int, db: DbSession,
                            x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    user = _user_by_tg(db, telegram_id)
    return AttendanceService(db, user.organization_id).student_history(student_id)


@router.get("/parent/child/{student_id}/payments", response_model=list[PaymentOut])
def parent_child_payments(student_id: int, telegram_id: int, db: DbSession,
                          x_bot_token: str | None = Header(default=None)):
    _auth(x_bot_token)
    user = _user_by_tg(db, telegram_id)
    from app.services.payment_service import PaymentService
    return PaymentService(db, user.organization_id).student_history(student_id)
