"""Bilingual (uz/en) bot strings."""
from locales.uz import UZ
from locales.en import EN

TRANSLATIONS = {"uz": UZ, "en": EN}


def tr(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in TRANSLATIONS else "uz"
    text = TRANSLATIONS[lang].get(key) or TRANSLATIONS["uz"].get(key, key)
    return text.format(**kwargs) if kwargs else text
