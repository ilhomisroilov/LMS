"""Reply & inline keyboards (bilingual)."""
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)

from locales import tr


def phone_request_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tr(lang, "share_phone"), request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True,
    )


def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="lang:uz"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    ]])


def student_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=tr(lang, "btn_my_groups")),
         KeyboardButton(text=tr(lang, "btn_my_attendance"))],
        [KeyboardButton(text=tr(lang, "btn_my_payments")),
         KeyboardButton(text=tr(lang, "btn_my_lessons"))],
        [KeyboardButton(text=tr(lang, "btn_language"))],
    ])


def teacher_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=tr(lang, "btn_groups")),
         KeyboardButton(text=tr(lang, "btn_take_attendance"))],
        [KeyboardButton(text=tr(lang, "btn_language"))],
    ])


def parent_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=tr(lang, "btn_children"))],
        [KeyboardButton(text=tr(lang, "btn_language"))],
    ])


def menu_for(role: str, lang: str) -> ReplyKeyboardMarkup:
    return {
        "teacher": teacher_menu, "parent": parent_menu,
    }.get(role, student_menu)(lang)


def groups_inline(groups: list[dict], prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=g["name"], callback_data=f"{prefix}:{g['id']}")]
            for g in groups]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def attendance_marks_kb(student_id: int, lang: str) -> InlineKeyboardMarkup:
    from locales import tr as _t
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=_t(lang, "status_present"), callback_data=f"mark:{student_id}:present"),
        InlineKeyboardButton(text=_t(lang, "status_late"), callback_data=f"mark:{student_id}:late"),
        InlineKeyboardButton(text=_t(lang, "status_absent"), callback_data=f"mark:{student_id}:absent"),
    ]])
