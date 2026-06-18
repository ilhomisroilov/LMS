"""Authentication: /start, contact sharing, language switch."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.menus import language_kb, menu_for, phone_request_kb
from locales import tr
from services.api_client import api
from services.session import get_session, set_session, update_language
from states import Auth

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    tid = message.from_user.id
    session = await get_session(tid)
    if session:
        await message.answer(
            tr(session["language"], f"menu_{session['role']}")
            if session["role"] in {"student", "teacher", "parent"} else "Menu",
            reply_markup=menu_for(session["role"], session["language"]),
        )
        return
    lang = (message.from_user.language_code or "uz")[:2]
    lang = lang if lang in {"uz", "en"} else "uz"
    await state.set_state(Auth.waiting_phone)
    await state.update_data(lang=lang)
    await message.answer(tr(lang, "welcome"), reply_markup=phone_request_kb(lang))


@router.message(Auth.waiting_phone, F.contact)
async def on_contact(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    status, resp = await api.link(phone, message.from_user.id)
    if status != 200 or not resp:
        await message.answer(tr(lang, "not_linked"))
        return
    role, name = resp["role"], resp["full_name"]
    # honour any language already stored on the account
    lang = resp.get("language") or lang
    set_session(message.from_user.id, role, lang, name)
    await state.clear()
    await message.answer(
        tr(lang, "linked", name=name, role=tr(lang, f"role_{role}")),
        reply_markup=menu_for(role, lang),
    )


@router.message(F.text.in_({"🌐 Til", "🌐 Language"}))
@router.message(Command("language"))
async def choose_language(message: Message) -> None:
    lang = await _lang(message.from_user.id)
    await message.answer(tr(lang, "choose_language"), reply_markup=language_kb())


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(cb: CallbackQuery) -> None:
    lang = cb.data.split(":", 1)[1]
    tid = cb.from_user.id
    await api.set_language(tid, lang)
    update_language(tid, lang)
    session = await get_session(tid)
    role = session["role"] if session else "student"
    await cb.message.answer(tr(lang, "language_set"), reply_markup=menu_for(role, lang))
    await cb.answer()


async def _lang(tid: int) -> str:
    s = await get_session(tid)
    return s["language"] if s else "uz"
