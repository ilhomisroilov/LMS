"""Teacher data access."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.teacher import Teacher
from app.repositories.base import BaseRepository


class TeacherRepository(BaseRepository[Teacher]):
    def __init__(self, db: Session) -> None:
        super().__init__(Teacher, db)

    def list_full(self, *, skip: int, limit: int, org_id: int | None = None) -> list[Teacher]:
        stmt = select(Teacher).options(joinedload(Teacher.user)).offset(skip).limit(limit)
        if org_id is not None:
            stmt = stmt.where(Teacher.organization_id == org_id)
        return list(
            self.db.scalars(stmt).unique().all()
        )

    def get_with_user(self, teacher_id: int, org_id: int | None = None) -> Teacher | None:
        stmt = select(Teacher).options(joinedload(Teacher.user)).where(Teacher.id == teacher_id)
        if org_id is not None:
            stmt = stmt.where(Teacher.organization_id == org_id)
        return self.db.scalar(stmt)

    def get_by_user_id(self, user_id: int) -> Teacher | None:
        return self.db.scalar(select(Teacher).where(Teacher.user_id == user_id))

    def count_for_org(self, org_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Teacher)
        if org_id is not None:
            stmt = stmt.where(Teacher.organization_id == org_id)
        return self.db.scalar(stmt) or 0
