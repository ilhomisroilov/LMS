"""Group data access."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.group import Group, GroupStudent
from app.models.student import Student
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository[Group]):
    def __init__(self, db: Session) -> None:
        super().__init__(Group, db)

    def get_full(self, group_id: int, org_id: int | None = None) -> Group | None:
        stmt = (
            select(Group)
            .options(joinedload(Group.teacher), joinedload(Group.course))
            .where(Group.id == group_id)
        )
        if org_id is not None:
            stmt = stmt.where(Group.organization_id == org_id)
        return self.db.scalar(stmt)

    def list_full(self, *, skip: int, limit: int, org_id: int | None = None) -> list[Group]:
        stmt = (
            select(Group)
            .options(joinedload(Group.teacher), joinedload(Group.course))
            .order_by(Group.id)
            .offset(skip).limit(limit)
        )
        if org_id is not None:
            stmt = stmt.where(Group.organization_id == org_id)
        return list(
            self.db.scalars(stmt).unique().all()
        )

    def count_for_org(self, org_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Group)
        if org_id is not None:
            stmt = stmt.where(Group.organization_id == org_id)
        return self.db.scalar(stmt) or 0

    def student_count(self, group_id: int) -> int:
        return self.db.scalar(
            select(func.count()).select_from(GroupStudent).where(GroupStudent.group_id == group_id)
        ) or 0

    def students(self, group_id: int, org_id: int | None = None) -> list[Student]:
        stmt = (
            select(Student)
            .join(GroupStudent, GroupStudent.student_id == Student.id)
            .options(joinedload(Student.user))
            .where(GroupStudent.group_id == group_id)
        )
        if org_id is not None:
            stmt = stmt.where(Student.organization_id == org_id)
        return list(
            self.db.scalars(stmt).unique().all()
        )

    def link_exists(self, group_id: int, student_id: int) -> bool:
        return self.db.scalar(
            select(GroupStudent.id).where(
                GroupStudent.group_id == group_id, GroupStudent.student_id == student_id
            )
        ) is not None

    def groups_for_teacher(self, teacher_id: int, org_id: int | None = None) -> list[Group]:
        stmt = select(Group).where(Group.teacher_id == teacher_id)
        if org_id is not None:
            stmt = stmt.where(Group.organization_id == org_id)
        return list(self.db.scalars(stmt).all())
