"""Shared FastAPI dependencies: DB session, current user, RBAC guards, language."""
from typing import Annotated, Callable

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.i18n import t
from app.core.security import ACCESS, decode_token
from app.models.user import User
from app.models.role import RoleName

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login/oauth")

DbSession = Annotated[Session, Depends(get_db)]


def get_language(accept_language: str | None = Header(default=None)) -> str:
    """Resolve UI language from the Accept-Language header (uz default)."""
    if accept_language:
        lang = accept_language.split(",")[0].split("-")[0].strip().lower()
        if lang in {"uz", "en"}:
            return lang
    return settings.DEFAULT_LANGUAGE


Language = Annotated[str, Depends(get_language)]


def get_current_user(
    db: DbSession,
    lang: Language,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.invalid_token", lang),
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, t("auth.invalid_token", lang))
    # Force-logout-all: a token minted before token_version was bumped is dead.
    if payload.get("tv", 0) != user.token_version:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, t("auth.invalid_token", lang),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active or user.status in {"suspended", "disabled"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("auth.inactive_user", lang))
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: RoleName) -> Callable[..., User]:
    """Dependency factory enforcing that the current user has one of `roles`."""
    allowed = {r.value if isinstance(r, RoleName) else r for r in roles}

    def _guard(user: CurrentUser, lang: Language) -> User:
        if user.role.name not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, t("auth.forbidden", lang))
        return user

    return _guard
