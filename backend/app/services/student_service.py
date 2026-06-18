from __future__ import annotations
"""Student CRM business logic (tenant-scoped, v1.2)."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.group import Group, GroupStudent
from app.models.role import RoleName
from app.models.student import Student
from app.models.user import User
from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError


class StudentService:
    def __init__(self, db: Session, org_id: int | None = None) -> None:
        self.db = db
        self.org_id = org_id
        self.repo = StudentRepository(db)
        self.users = UserRepository(db)

    def _to_out(self, s: Student, group_ids: list[int] | None = None) -> StudentOut:
        return StudentOut(
            id=s.id, user_id=s.user_id, full_name=s.user.full_name, phone=s.user.phone,
            parent_phone=s.parent_phone, status=s.status, parent_id=s.parent_id,
            created_at=s.created_at,
            group_ids=group_ids if group_ids is not None else self.repo.group_ids(s.id),
        )

    def list(self, *, q=None, status=None, group_id=None, page=1, size=20):
        skip = (page - 1) * size
        rows, total = self.repo.search(
            q=q, status=status, group_id=group_id, skip=skip, limit=size, org_id=self.org_id
        )
        gmap = self.repo.group_ids_for([s.id for s in rows])
        return [self._to_out(s, gmap.get(s.id, [])) for s in rows], total

    def get(self, student_id: int) -> StudentOut:
        s = self.repo.get_with_user(student_id, org_id=self.org_id)
        if not s:
            raise NotFoundError()
        return self._to_out(s)

    def create(self, data: StudentCreate) -> StudentOut:
        if self.org_id is None:
            raise ServiceError("common.bad_request")
        if self.users.get_by_phone(data.phone):
            raise ConflictError("students.phone_exists")
        if data.group_id:
            grp = self.db.get(Group, data.group_id)
            if not grp or grp.organization_id != self.org_id:
                raise NotFoundError("groups.not_found")
        try:
            role = self.users.get_role(RoleName.student)
            user = User(
                full_name=data.full_name, phone=data.phone,
                hashed_password=hash_password(data.password),
                language=data.language, role_id=role.id,
                organization_id=self.org_id, status="active",
            )
            self.users.add(user)
            self.db.flush()
            student = Student(
                user_id=user.id, organization_id=self.org_id,
                parent_phone=data.parent_phone, status=data.status, parent_id=data.parent_id,
            )
            self.repo.add(student)
            self.db.flush()
            if data.group_id:
                self.db.add(GroupStudent(group_id=data.group_id, student_id=student.id))
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("students.phone_exists") from None
        return self.get(student.id)

    def update(self, student_id: int, data: StudentUpdate) -> StudentOut:
        s = self.repo.get_with_user(student_id, org_id=self.org_id)
        if not s:
            raise NotFoundError()
        if data.full_name is not None:
            s.user.full_name = data.full_name
        if data.phone is not None:
            s.user.phone = data.phone
        if data.language is not None:
            s.user.language = data.language
        for field in ("parent_phone", "status", "parent_id"):
            val = getattr(data, field)
            if val is not None:
                setattr(s, field, val)
        self.db.commit()
        return self.get(student_id)

    def delete(self, student_id: int) -> None:
        s = self.repo.get_with_user(student_id, org_id=self.org_id)
        if not s:
            raise NotFoundError()
        self.db.delete(s.user)
        self.db.commit()
