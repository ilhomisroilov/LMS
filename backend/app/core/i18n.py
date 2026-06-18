"""Minimal backend i18n: translatable message keys (uz default, en)."""
from app.core.config import settings

MESSAGES: dict[str, dict[str, str]] = {
    "auth.invalid_credentials": {
        "uz": "Telefon raqami yoki parol noto‘g‘ri",
        "en": "Invalid phone number or password",
    },
    "auth.inactive_user": {
        "uz": "Foydalanuvchi faol emas",
        "en": "User is inactive",
    },
    "auth.not_authenticated": {
        "uz": "Avtorizatsiya talab qilinadi",
        "en": "Not authenticated",
    },
    "auth.forbidden": {
        "uz": "Ruxsat etilmagan",
        "en": "Permission denied",
    },
    "auth.invalid_token": {
        "uz": "Token yaroqsiz yoki muddati o‘tgan",
        "en": "Invalid or expired token",
    },
    "common.not_found": {
        "uz": "Topilmadi",
        "en": "Not found",
    },
    "common.already_exists": {
        "uz": "Allaqachon mavjud",
        "en": "Already exists",
    },
    "students.phone_exists": {
        "uz": "Bu telefon raqami bilan foydalanuvchi allaqachon mavjud",
        "en": "A user with this phone number already exists",
    },
    "rate_limit.exceeded": {
        "uz": "So‘rovlar soni limitidan oshib ketdi",
        "en": "Rate limit exceeded",
    },
}


def t(key: str, lang: str | None = None) -> str:
    """Translate a message key into the requested language."""
    lang = (lang or settings.DEFAULT_LANGUAGE).lower()
    entry = MESSAGES.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get(settings.DEFAULT_LANGUAGE) or key
