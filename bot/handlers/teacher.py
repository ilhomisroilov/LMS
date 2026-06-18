"""Teacher menu: view groups, students, and take attendance via inline marking."""
from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.menus import attendance_marks_kb, groups_inline
from locales import tr
from services.api_client import api
from services.session import lang_of
from states import TakeAttendance

router = Router()


def _btn(*keys):
    return F.text.in_({tr(l, k) for l in ("uz", "en") for k in keys})


@router.message(_btn("btn_groups"))
async def groups(message: Message) -> None:
    lang = await lang_of(message.from_user.id)
    status, data = await api.teacher_groups(message.from_user.id)
    if status != 200:
        return await message.answer(tr(lang, "error"))
    if not data:
        return await message.answer(tr(lang, "no_groups"))
    lines = [tr(lang, "group_line", name=g["name"], course=g.get("course_name") or "-",
                days=g.get("schedule_days") or "", time=g.get("schedule_time") or "")
             for g in data]
    await message.answer(tr(lang, "groups_title") + "\n" + "\n".join(lines))


@router.message(_btn("btn_take_attendance"))
async def start_attendance(message: Message, state: FSMContext) -> None:
    lang = await lang_of(message.from_user.id)
    status, data = await api.teacher_groups(message.from_user.id)
    if not data:
        return await message.answer(tr(lang, "no_groups"))
    await state.set_state(TakeAttendance.selecting_group)
    await message.answer(tr(lang, "select_group_attendance"),
                         reply_markup=groups_inline(data, "att_grp"))


@router.callback_query(TakeAttendance.selecting_group, F.data.startswith("att_grp:"))
async def pick_group(cb: CallbackQuery, state: FSMContext) -> None:
    lang = await lang_of(cb.from_user.id)
    group_id = int(cb.data.split(":")[1])
    status, students = await api.teacher_group_students(group_id, cb.from_user.id)
    if not students:
        await cb.message.answer(tr(lang, "no_students"))
        await state.clear()
        return await cb.answer()
    await state.set_state(TakeAttendance.marking)
    await state.update_data(group_id=group_id, records={}, total=len(students))
    await cb.message.answer(tr(lang, "students_title"))
    for s in students:
        await cb.message.answer(s["full_name"], reply_markup=attendance_marks_kb(s["id"], lang))
    await cb.answer()


@router.callback_query(TakeAttendance.marking, F.data.startswith("mark:"))
async def mark_student(cb: CallbackQuery, state: FSMContext) -> None:
    lang = await lang_of(cb.from_user.id)
    _, sid, status = cb.data.split(":")
    data = await state.get_data()
    records = data.get("records", {})
    records[sid] = status
    await state.update_data(records=records)
    await cb.answer(tr(lang, {"present": "status_present", "absent": "status_absent",
                              "late": "status_late"}[status]))
    # When all students marked, submit
    if len(records) >= data.get("total", 0):
        payload = [{"student_id": int(k), "status": v} for k, v in records.items()]
        await api.teacher_mark_attendance(
            cb.from_user.id, data["group_id"], date.today().isoformat(), payload
        )
        await cb.message.answer("✅ " + tr(lang, "attendance_title"))
        await state.clear()
