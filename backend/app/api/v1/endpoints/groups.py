"""Group / cohort endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.authz import AuthContext, require_permission
from app.core.deps import DbSession, Language
from app.core.i18n import t
from app.core.permissions import Perm
from app.schemas.common import Page
from app.schemas.group import AssignStudents, GroupCreate, GroupOut, GroupUpdate
from app.schemas.student import StudentOut
from app.services.exceptions import ServiceError
from app.services.group_service import GroupService

router = APIRouter(prefix="/groups", tags=["groups"])
CanRead = Depends(require_permission(Perm.GROUP_READ))
CanWrite = Depends(require_permission(Perm.GROUP_WRITE))


@router.get("", response_model=Page[GroupOut])
def list_groups(db: DbSession, ctx: AuthContext = CanRead, page: int = 1, size: int = 50):
    items, total = GroupService(db, ctx.organization_id).list(page=page, size=size)
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=GroupOut, status_code=201)
def create_group(data: GroupCreate, db: DbSession, ctx: AuthContext = CanWrite):
    return GroupService(db, ctx.organization_id).create(data)


@router.get("/{group_id}", response_model=GroupOut)
def get_group(group_id: int, db: DbSession, lang: Language, ctx: AuthContext = CanRead):
    try:
        return GroupService(db, ctx.organization_id).get(group_id)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.patch("/{group_id}", response_model=GroupOut)
def update_group(group_id: int, data: GroupUpdate, db: DbSession, lang: Language,
                 ctx: AuthContext = CanWrite):
    try:
        return GroupService(db, ctx.organization_id).update(group_id, data)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.delete("/{group_id}", status_code=204)
def delete_group(group_id: int, db: DbSession, lang: Language, ctx: AuthContext = CanWrite):
    try:
        GroupService(db, ctx.organization_id).delete(group_id)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.get("/{group_id}/students", response_model=list[StudentOut])
def group_students(group_id: int, db: DbSession, lang: Language, ctx: AuthContext = CanRead):
    try:
        return GroupService(db, ctx.organization_id).students(group_id)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.post("/{group_id}/students", response_model=GroupOut)
def assign_students(group_id: int, data: AssignStudents, db: DbSession, lang: Language,
                    ctx: AuthContext = CanWrite):
    try:
        return GroupService(db, ctx.organization_id).assign_students(group_id, data.student_ids)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.delete("/{group_id}/students/{student_id}", status_code=204)
def remove_student(group_id: int, student_id: int, db: DbSession, ctx: AuthContext = CanWrite):
    GroupService(db, ctx.organization_id).remove_student(group_id, student_id)
