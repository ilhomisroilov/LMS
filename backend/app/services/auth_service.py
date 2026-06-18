from __future__ import annotations
"""Authentication: login, refresh rotation + family revocation, invites, logout."""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.config import settings
from app.core.security import (
    ACCESS, REFRESH, create_access_token, create_refresh_token,
    decode_token, generate_secret, hash_password, hash_token,
    new_family_id, verify_password,
)
from app.models.invite import Invite
from app.models.parent import Parent
from app.models.refresh_token import RefreshToken
from app.models.role import RoleName
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, Token
from app.services.exceptions import AuthError, ConflictError, NotFoundError


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.tokens = TokenRepository(db)

    # ------------------------------------------------------------------ login
    def authenticate(self, phone: str, password: str) -> User:
        user = self.users.get_by_phone(phone)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthError("auth.invalid_credentials")
        if user.status == "invited":
            # Account exists but invite not yet accepted -> no usable password.
            raise AuthError("auth.invalid_credentials")
        if not user.is_active or user.status in {"suspended", "disabled"}:
            raise AuthError("auth.inactive_user", 403)
        return user

    def _create_tokens(self, user: User, family_id: str) -> tuple[Token, RefreshToken]:
        access = create_access_token(
            user.id, user.role.name,
            organization_id=user.organization_id,
            branch_id=user.branch_id,
            token_version=user.token_version,
        )
        refresh = create_refresh_token(user.id, family_id)
        row = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh),
            family_id=family_id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.tokens.add(row)
        self.db.flush()
        token = Token(
            access_token=access, refresh_token=refresh,
            must_change_password=user.must_change_password,
        )
        return token, row

    def login(self, phone: str, password: str) -> Token:
        user = self.authenticate(phone, password)
        user.last_login_at = datetime.now(timezone.utc)
        token, _ = self._create_tokens(user, new_family_id())
        write_audit(
            self.db, action="auth.login", organization_id=user.organization_id,
            actor_user_id=user.id, actor_role=user.role.name,
            entity_type="user", entity_id=user.id,
        )
        self.db.commit()
        return token

    # ---------------------------------------------------------------- refresh
    def refresh(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != REFRESH:
            raise AuthError("auth.invalid_token")
        stored = self.tokens.get_by_hash(hash_token(refresh_token))
        if not stored:
            raise AuthError("auth.invalid_token")

        # Reuse / theft detection: presenting an already-revoked token kills the
        # whole family (all sessions descended from that login).
        if stored.revoked:
            self.tokens.revoke_family(stored.family_id)
            write_audit(
                self.db, action="auth.token_reuse_detected",
                organization_id=None, actor_user_id=stored.user_id,
                entity_type="refresh_token", entity_id=stored.id,
            )
            self.db.commit()
            raise AuthError("auth.invalid_token")

        if stored.expires_at < datetime.now(timezone.utc):
            raise AuthError("auth.invalid_token")

        user = self.users.get(int(payload["sub"]))
        if not user or not user.is_active or user.status in {"suspended", "disabled"}:
            raise AuthError("auth.invalid_token")

        # Rotate within the same family; link old -> new and revoke old.
        token, new_row = self._create_tokens(user, stored.family_id)
        self.tokens.revoke(stored, replaced_by_id=new_row.id)
        write_audit(
            self.db, action="auth.token_refreshed",
            organization_id=user.organization_id, actor_user_id=user.id,
            actor_role=user.role.name, entity_type="refresh_token", entity_id=new_row.id,
        )
        self.db.commit()
        return token

    # ----------------------------------------------------------------- logout
    def logout(self, user_id: int) -> None:
        self.tokens.revoke_all_for_user(user_id)
        user = self.users.get(user_id)
        write_audit(
            self.db, action="auth.logout",
            organization_id=user.organization_id if user else None,
            actor_user_id=user_id, actor_role=user.role.name if user else None,
        )
        self.db.commit()

    def logout_all_sessions(self, user_id: int) -> None:
        """Force-logout every session: revoke refresh tokens AND invalidate
        outstanding access tokens by bumping token_version (spec §12.1)."""
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError()
        self.tokens.revoke_all_for_user(user_id)
        user.token_version += 1
        write_audit(
            self.db, action="auth.logout_all", organization_id=user.organization_id,
            actor_user_id=user_id, actor_role=user.role.name,
        )
        self.db.commit()

    # ------------------------------------------------------- password / invite
    def change_password(self, user: User, old_password: str, new_password: str) -> None:
        if not verify_password(old_password, user.hashed_password):
            raise AuthError("auth.invalid_credentials")
        user.hashed_password = hash_password(new_password)
        user.must_change_password = False
        user.token_version += 1  # invalidate other sessions on password change
        self.tokens.revoke_all_for_user(user.id)
        write_audit(
            self.db, action="auth.password_changed", organization_id=user.organization_id,
            actor_user_id=user.id, actor_role=user.role.name, entity_type="user", entity_id=user.id,
        )
        self.db.commit()

    def create_invite(self, user_id: int, *, created_by: int | None = None,
                      ttl_hours: int = 72) -> str:
        """Issue a single-use invite token for a user. Returns the RAW token
        (shown once); only its hash is stored."""
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError()
        raw = generate_secret()
        self.db.add(Invite(
            organization_id=user.organization_id, user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
            created_by=created_by,
        ))
        self.db.commit()
        return raw

    def accept_invite(self, raw_token: str, new_password: str) -> Token:
        invite = self.db.query(Invite).filter(
            Invite.token_hash == hash_token(raw_token)
        ).one_or_none()
        if not invite or invite.accepted_at is not None:
            raise AuthError("auth.invalid_token")
        if invite.expires_at < datetime.now(timezone.utc):
            raise AuthError("auth.invalid_token")
        user = self.users.get(invite.user_id)
        if not user:
            raise AuthError("auth.invalid_token")
        user.hashed_password = hash_password(new_password)
        user.status = "active"
        user.is_active = True
        user.must_change_password = False
        invite.accepted_at = datetime.now(timezone.utc)
        token, _ = self._create_tokens(user, new_family_id())
        write_audit(
            self.db, action="auth.invite_accepted", organization_id=user.organization_id,
            actor_user_id=user.id, actor_role=user.role.name, entity_type="user", entity_id=user.id,
        )
        self.db.commit()
        return token

    # --------------------------------------------------------------- register
    def register(self, data: RegisterRequest) -> User:
        """Public registration (back-compat). Assigns the user to the default
        organization. In production, prefer admin-created users + invites."""
        if self.users.get_by_phone(data.phone):
            raise ConflictError("common.already_exists")
        role = self.users.get_role(data.role)
        if not role:
            raise AuthError("auth.forbidden", 400)
        org_id = self.users.default_organization_id()
        if org_id is None:
            raise AuthError("auth.forbidden", 400)
        user = User(
            full_name=data.full_name, phone=data.phone,
            hashed_password=hash_password(data.password),
            language=data.language, role_id=role.id,
            organization_id=org_id, status="active",
        )
        self.users.add(user)
        self.db.flush()
        if role.name == RoleName.student.value:
            self.db.add(Student(user_id=user.id, organization_id=org_id))
        elif role.name == RoleName.teacher.value:
            self.db.add(Teacher(user_id=user.id, organization_id=org_id))
        elif role.name == RoleName.parent.value:
            self.db.add(Parent(user_id=user.id, organization_id=org_id))
        self.db.commit()
        self.db.refresh(user)
        return user
