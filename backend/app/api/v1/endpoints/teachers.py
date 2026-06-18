"""Teacher management endpoints (admin only for writes)."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.authz import AuthContext, require_permission
from app.core.deps import DbSession, Language
from app.core.i18n import t
from app.core.permissions import Perm
from app.schemas.common import Page
from app.schemas.teacher import TeacherCreate, TeacherOut, TeacherUpdate
from app.services.exceptions import ServiceError
from app.services.teacher_service import TeacherService

router = APIRouter(prefix="/teachers", tags=["teachers"])
CanRead = Depends(require_permission(Perm.TEACHER_READ))
CanWrite = Depends(require_permission(Perm.TEACHER_WRITE))


@router.get("", response_model=Page[TeacherOut])
def list_teachers(db: DbSession, ctx: AuthContext = CanRead, page: int = 1, size: int = 50):
    items, total = TeacherService(db, ctx.organization_id).list(page=page, size=size)
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=TeacherOut, status_code=201)
def create_teacher(data: TeacherCreate, db: DbSession, lang: Language,
                   ctx: AuthContext = CanWrite):
    try:
        return TeacherService(db, ctx.organization_id).create(data)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.get("/{teacher_id}", response_model=TeacherOut)
def get_teacher(teacher_id: int, db: DbSession, lang: Language, ctx: AuthContext = CanRead):
    try:
        return TeacherService(db, ctx.organization_id).get(teacher_id)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.patch("/{teacher_id}", response_model=TeacherOut)
def update_teacher(teacher_id: int, data: TeacherUpdate, db: DbSession, lang: Language,
                   ctx: AuthContext = CanWrite):
    try:
        return TeacherService(db, ctx.organization_id).update(teacher_id, data)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.delete("/{teacher_id}", status_code=204)
def delete_teacher(teacher_id: int, db: DbSession, lang: Language,
                   ctx: AuthContext = CanWrite):
    try:
        TeacherService(db, ctx.organization_id).delete(teacher_id)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))
