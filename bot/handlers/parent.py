"""Parent menu handlers: children list + per-child attendance & payments."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from locales import tr
from services.api_client import api
from services.session import lang_of

router = Router()
_STATUS = {"present": "status_present", "absent": "status_absent", "late": "status_late",
           "paid": "status_paid", "unpaid": "status_unpaid", "partial": "status_partial"}


def _btn(*keys):
    return F.text.in_({tr(l, k) for l in ("uz", "en") for k in keys})


@router.message(_btn("btn_children"))
async def children(message: Message) -> None:
    lang = await lang_of(message.from_user.id)
    status, data = await api.parent_children(message.from_user.id)
    if status != 200:
        return await message.answer(tr(lang, "error"))
    if not data:
        return await message.answer(tr(lang, "no_children"))
    rows = [[InlineKeyboardButton(text=f'📅 {c["full_name"]}', callback_data=f'patt:{c["id"]}'),
             InlineKeyboardButton(text="💳", callback_data=f'ppay:{c["id"]}')] for c in data]
    await message.answer(tr(lang, "students_title"),
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("patt:"))
async def child_attendance(cb: CallbackQuery) -> None:
    lang = await lang_of(cb.from_user.id)
    sid = int(cb.data.split(":")[1])
    status, data = await api.parent_child_attendance(sid, cb.from_user.id)
    if not data:
        await cb.message.answer(tr(lang, "no_attendance"))
    else:
        lines = [tr(lang, "att_line", date=a["lesson_date"],
                    status=tr(lang, _STATUS.get(a["status"], a["status"]))) for a in data[:30]]
        await cb.message.answer(tr(lang, "attendance_title") + "\n" + "\n".join(lines))
    await cb.answer()


@router.callback_query(F.data.startswith("ppay:"))
async def child_payments(cb: CallbackQuery) -> None:
    lang = await lang_of(cb.from_user.id)
    sid = int(cb.data.split(":")[1])
    status, data = await api.parent_child_payments(sid, cb.from_user.id)
    if not data:
        await cb.message.answer(tr(lang, "no_payments"))
    else:
        lines = [tr(lang, "pay_line", month=p["month"], amount=f'{float(p["amount"]):,.0f}',
                    status=tr(lang, _STATUS.get(p["status"], p["status"]))) for p in data]
        await cb.message.answer(tr(lang, "payments_title") + "\n" + "\n".join(lines))
    await cb.answer()
