"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import CurrentUser, DbSession, Language
from app.core.i18n import t
from app.core.permissions import permission_strings_for
from app.schemas.auth import (
    AcceptInviteRequest, ChangePasswordRequest, LinkedEntities, LoginRequest,
    MeOut, RefreshRequest, RegisterRequest, Token, UserOut,
)
from app.services.auth_service import AuthService
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/auth", tags=["auth"])


def _handle(exc: ServiceError, lang: str) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=t(exc.msg_key, lang))


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: DbSession, lang: Language):
    try:
        return AuthService(db).login(data.phone, data.password)
    except ServiceError as e:
        raise _handle(e, lang)


@router.post("/login/oauth", response_model=Token, include_in_schema=False)
def login_oauth(db: DbSession, lang: Language, form: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password-flow variant so Swagger 'Authorize' works (username=phone)."""
    try:
        return AuthService(db).login(form.username, form.password)
    except ServiceError as e:
        raise _handle(e, lang)


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest, db: DbSession, lang: Language):
    try:
        return AuthService(db).register(data)
    except ServiceError as e:
        raise _handle(e, lang)


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshRequest, db: DbSession, lang: Language):
    try:
        return AuthService(db).refresh(data.refresh_token)
    except ServiceError as e:
        raise _handle(e, lang)


@router.post("/accept-invite", response_model=Token)
def accept_invite(data: AcceptInviteRequest, db: DbSession, lang: Language):
    """Redeem a single-use invite token and set the account password."""
    try:
        return AuthService(db).accept_invite(data.token, data.new_password)
    except ServiceError as e:
        raise _handle(e, lang)


@router.post("/change-password", status_code=204)
def change_password(data: ChangePasswordRequest, db: DbSession, user: CurrentUser, lang: Language):
    try:
        AuthService(db).change_password(user, data.old_password, data.new_password)
    except ServiceError as e:
        raise _handle(e, lang)


@router.post("/logout", status_code=204)
def logout(db: DbSession, user: CurrentUser):
    AuthService(db).logout(user.id)


@router.post("/logout-all", status_code=204)
def logout_all(db: DbSession, user: CurrentUser):
    """Revoke every session for the current user (refresh + access tokens)."""
    AuthService(db).logout_all_sessions(user.id)


@router.get("/me", response_model=MeOut)
def me(user: CurrentUser):
    linked = LinkedEntities()
    if user.student:
        linked.student_id = user.student.id
    if user.teacher:
        linked.teacher_id = user.teacher.id
        linked.teacher_group_ids = [g.id for g in user.teacher.groups]
    if user.parent:
        linked.parent_id = user.parent.id
        linked.child_student_ids = [c.id for c in user.parent.children]
    return MeOut(
        id=user.id, full_name=user.full_name, phone=user.phone,
        is_active=user.is_active, language=user.language,
        role_id=user.role_id, role=user.role.name,
        organization_id=user.organization_id, branch_id=user.branch_id,
        must_change_password=user.must_change_password,
        permissions=permission_strings_for(user.role.name),
        linked=linked,
    )
