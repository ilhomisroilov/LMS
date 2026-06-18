"""Student data access with search & filtering (tenant-aware)."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.group import GroupStudent
from app.models.student import Student
from app.models.user import User
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    def __init__(self, db: Session) -> None:
        super().__init__(Student, db)

    def get_with_user(self, student_id: int, *, org_id: int | None = None) -> Student | None:
        stmt = select(Student).options(joinedload(Student.user)).where(Student.id == student_id)
        if org_id is not None:  # layer-1 tenant filter
            stmt = stmt.where(Student.organization_id == org_id)
        return self.db.scalar(stmt)

    def get_by_user_id(self, user_id: int) -> Student | None:
        return self.db.scalar(select(Student).where(Student.user_id == user_id))

    def search(self, *, q: str | None, status: str | None, group_id: int | None,
               skip: int, limit: int, org_id: int | None = None) -> tuple[list[Student], int]:
        stmt = select(Student).join(User, Student.user_id == User.id).options(
            joinedload(Student.user)
        )
        if org_id is not None:  # layer-1 tenant filter
            stmt = stmt.where(Student.organization_id == org_id)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(User.full_name.ilike(like), User.phone.ilike(like)))
        if status:
            stmt = stmt.where(Student.status == status)
        if group_id:
            stmt = stmt.join(GroupStudent, GroupStudent.student_id == Student.id).where(
                GroupStudent.group_id == group_id
            )
        total = self.db.scalar(
            select(func.count()).select_from(stmt.order_by(None).subquery())
        ) or 0
        rows = list(self.db.scalars(stmt.offset(skip).limit(limit)).unique().all())
        return rows, total

    def group_ids(self, student_id: int) -> list[int]:
        return list(
            self.db.scalars(
                select(GroupStudent.group_id).where(GroupStudent.student_id == student_id)
            ).all()
        )

    def group_ids_for(self, student_ids: list[int]) -> dict[int, list[int]]:
        """Batch-fetch group ids for many students in a single query (no N+1)."""
        if not student_ids:
            return {}
        rows = self.db.execute(
            select(GroupStudent.student_id, GroupStudent.group_id).where(
                GroupStudent.student_id.in_(student_ids)
            )
        ).all()
        out: dict[int, list[int]] = {sid: [] for sid in student_ids}
        for sid, gid in rows:
            out.setdefault(sid, []).append(gid)
        return out
