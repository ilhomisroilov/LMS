"""Refresh-token persistence: rotation, family revocation, reuse detection."""
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class TokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: Session) -> None:
        super().__init__(RefreshToken, db)

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )

    def revoke(self, row: RefreshToken, replaced_by_id: int | None = None) -> None:
        row.revoked = True
        row.revoked_at = datetime.now(timezone.utc)
        if replaced_by_id is not None:
            row.replaced_by_id = replaced_by_id
        self.db.flush()

    def revoke_family(self, family_id: str) -> None:
        """Revoke every token in a family (reuse/theft detection or logout)."""
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked.is_(False))
            .values(revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        self.db.flush()

    def revoke_all_for_user(self, user_id: int) -> None:
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        self.db.flush()
