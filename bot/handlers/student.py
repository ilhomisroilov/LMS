"""Student menu handlers: groups, attendance, payments, lessons."""
from aiogram import F, Router
from aiogram.types import Message

from locales import tr
from services.api_client import api
from services.session import lang_of

router = Router()

_STATUS = {"present": "status_present", "absent": "status_absent", "late": "status_late",
           "paid": "status_paid", "unpaid": "status_unpaid", "partial": "status_partial"}


def _btn(*keys):
    return F.text.in_({tr(l, k) for l in ("uz", "en") for k in keys})


@router.message(_btn("btn_my_groups"))
async def my_groups(message: Message) -> None:
    lang = await lang_of(message.from_user.id)
    status, data = await api.student_groups(message.from_user.id)
    if status != 200:
        return await message.answer(tr(lang, "error"))
    if not data:
        return await message.answer(tr(lang, "no_groups"))
    lines = [tr(lang, "group_line", name=g["name"], course=g.get("course_name") or "-",
                days=g.get("schedule_days") or "", time=g.get("schedule_time") or "")
             for g in data]
    await message.answer(tr(lang, "groups_title") + "\n" + "\n".join(lines))


@router.message(_btn("btn_my_attendance"))
async def my_attendance(message: Message) -> None:
    lang = await lang_of(message.from_user.id)
    status, data = await api.student_attendance(message.from_user.id)
    if status != 200:
        return await message.answer(tr(lang, "error"))
    if not data:
        return await message.answer(tr(lang, "no_attendance"))
    lines = [tr(lang, "att_line", date=a["lesson_date"],
                status=tr(lang, _STATUS.get(a["status"], a["status"]))) for a in data[:30]]
    await message.answer(tr(lang, "attendance_title") + "\n" + "\n".join(lines))


@router.message(_btn("btn_my_payments"))
async def my_payments(message: Message) -> None:
    lang = await lang_of(message.from_user.id)
    status, data = await api.student_payments(message.from_user.id)
    if status != 200:
        return await message.answer(tr(lang, "error"))
    if not data:
        return await message.answer(tr(lang, "no_payments"))
    lines = [tr(lang, "pay_line", month=p["month"],
                amount=f'{float(p["amount"]):,.0f}',
                status=tr(lang, _STATUS.get(p["status"], p["status"]))) for p in data]
    await message.answer(tr(lang, "payments_title") + "\n" + "\n".join(lines))


@router.message(_btn("btn_my_lessons"))
async def my_lessons(message: Message) -> None:
    lang = await lang_of(message.from_user.id)
    status, data = await api.student_lessons(message.from_user.id)
    if status != 200:
        return await message.answer(tr(lang, "error"))
    if not data:
        return await message.answer(tr(lang, "no_lessons"))
    lines = [tr(lang, "lesson_line", title=l["title"], ctype=l["content_type"],
                done=tr(lang, "done_yes") if l.get("completed") else tr(lang, "done_no"))
             for l in data]
    await message.answer(tr(lang, "lessons_title") + "\n" + "\n".join(lines))
