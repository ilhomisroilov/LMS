"""User & role data access."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Role, RoleName
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_phone(self, phone: str) -> User | None:
        return self.db.scalar(select(User).where(User.phone == phone))

    def default_organization_id(self) -> int | None:
        """Lowest-id organization — the default tenant for public registration."""
        return self.db.scalar(select(Organization.id).order_by(Organization.id).limit(1))

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return self.db.scalar(select(User).where(User.telegram_id == telegram_id))

    def get_role(self, name: RoleName | str) -> Role | None:
        value = name.value if isinstance(name, RoleName) else name
        return self.db.scalar(select(Role).where(Role.name == value))
