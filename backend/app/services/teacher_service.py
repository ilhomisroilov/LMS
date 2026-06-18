from __future__ import annotations
"""Teacher management."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.role import RoleName
from app.models.teacher import Teacher
from app.models.user import User
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository
from app.schemas.teacher import TeacherCreate, TeacherOut, TeacherUpdate
from app.services.exceptions import ConflictError, NotFoundError, ServiceError


class TeacherService:
    def __init__(self, db: Session, org_id: int | None = None) -> None:
        self.db = db
        self.org_id = org_id
        self.repo = TeacherRepository(db)
        self.users = UserRepository(db)

    def _to_out(self, t: Teacher) -> TeacherOut:
        return TeacherOut(
            id=t.id, user_id=t.user_id, full_name=t.user.full_name,
            phone=t.user.phone, salary=float(t.salary) if t.salary is not None else None,
            subjects=t.subjects,
        )

    def list(self, *, page=1, size=50):
        skip = (page - 1) * size
        rows = self.repo.list_full(skip=skip, limit=size, org_id=self.org_id)
        return [self._to_out(t) for t in rows], self.repo.count_for_org(self.org_id)

    def get(self, teacher_id: int) -> TeacherOut:
        t = self.repo.get_with_user(teacher_id, self.org_id)
        if not t:
            raise NotFoundError()
        return self._to_out(t)

    def create(self, data: TeacherCreate) -> TeacherOut:
        if self.org_id is None:
            raise ServiceError("common.bad_request")
        if self.users.get_by_phone(data.phone):
            raise ConflictError()
        try:
            role = self.users.get_role(RoleName.teacher)
            user = User(
                full_name=data.full_name, phone=data.phone,
                hashed_password=hash_password(data.password),
                language=data.language, role_id=role.id,
                organization_id=self.org_id, status="active",
            )
            self.users.add(user)
            self.db.flush()
            teacher = Teacher(
                user_id=user.id, organization_id=self.org_id,
                salary=data.salary, subjects=data.subjects,
            )
            self.repo.add(teacher)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError() from None
        return self.get(teacher.id)

    def update(self, teacher_id: int, data: TeacherUpdate) -> TeacherOut:
        t = self.repo.get_with_user(teacher_id, self.org_id)
        if not t:
            raise NotFoundError()
        if data.full_name is not None:
            t.user.full_name = data.full_name
        if data.phone is not None:
            t.user.phone = data.phone
        for field in ("salary", "subjects"):
            val = getattr(data, field)
            if val is not None:
                setattr(t, field, val)
        self.db.commit()
        return self.get(teacher_id)

    def delete(self, teacher_id: int) -> None:
        t = self.repo.get_with_user(teacher_id, self.org_id)
        if not t:
            raise NotFoundError()
        self.db.delete(t.user)
        self.db.commit()
