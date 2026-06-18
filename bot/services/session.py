"""Lightweight per-user session cache (telegram_id -> {role, language})."""
from services.api_client import api

_cache: dict[int, dict] = {}


async def get_session(telegram_id: int) -> dict | None:
    if telegram_id in _cache:
        return _cache[telegram_id]
    status, data = await api.me(telegram_id)
    if status == 200 and data:
        _cache[telegram_id] = {"role": data["role"], "language": data["language"],
                               "full_name": data["full_name"]}
        return _cache[telegram_id]
    return None


def set_session(telegram_id: int, role: str, language: str, full_name: str) -> None:
    _cache[telegram_id] = {"role": role, "language": language, "full_name": full_name}


def update_language(telegram_id: int, language: str) -> None:
    if telegram_id in _cache:
        _cache[telegram_id]["language"] = language


async def lang_of(telegram_id: int) -> str:
    s = await get_session(telegram_id)
    return s["language"] if s else "uz"
