"""Student CRM endpoints — tenant + permission + ownership scoped (v1.2)."""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.authz import AuthContext, ensure_student_access, require_permission
from app.core.deps import DbSession, Language
from app.core.i18n import t
from app.core.permissions import Perm
from app.repositories.student_repository import StudentRepository
from app.schemas.attendance import AttendanceOut
from app.schemas.common import Page
from app.schemas.payment import PaymentOut
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate
from app.services.attendance_service import AttendanceService
from app.services.exceptions import NotFoundError, ServiceError
from app.services.payment_service import PaymentService
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["students"])

CanRead = Depends(require_permission(Perm.STUDENT_READ))
CanWrite = Depends(require_permission(Perm.STUDENT_WRITE))


@router.get("", response_model=Page[StudentOut])
def list_students(db: DbSession, ctx: AuthContext = CanRead, q: str | None = None,
                  status: str | None = None, group_id: int | None = None,
                  page: int = 1, size: int = Query(20, le=100)):
    items, total = StudentService(db, ctx.organization_id).list(
        q=q, status=status, group_id=group_id, page=page, size=size
    )
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=StudentOut, status_code=201)
def create_student(data: StudentCreate, db: DbSession, lang: Language, ctx: AuthContext = CanWrite):
    try:
        return StudentService(db, ctx.organization_id).create(data)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: DbSession, lang: Language, ctx: AuthContext = CanRead):
    # Layer 1 (tenant) + layer 3 (ownership): a teacher only sees assigned students.
    s = StudentRepository(db).get_with_user(student_id, org_id=ctx.organization_id)
    if not s:
        raise HTTPException(404, t("common.not_found", lang))
    ensure_student_access(db, ctx, s)
    return StudentService(db, ctx.organization_id).get(student_id)


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentUpdate, db: DbSession, lang: Language,
                   ctx: AuthContext = CanWrite):
    try:
        return StudentService(db, ctx.organization_id).update(student_id, data)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int, db: DbSession, lang: Language, ctx: AuthContext = CanWrite):
    try:
        StudentService(db, ctx.organization_id).delete(student_id)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))


@router.get("/{student_id}/attendance", response_model=list[AttendanceOut])
def student_attendance(student_id: int, db: DbSession, lang: Language, ctx: AuthContext = CanRead):
    s = StudentRepository(db).get_with_user(student_id, org_id=ctx.organization_id)
    if not s:
        raise HTTPException(404, t("common.not_found", lang))
    ensure_student_access(db, ctx, s)
    return AttendanceService(db, ctx.organization_id).student_history(student_id)


@router.get("/{student_id}/payments", response_model=list[PaymentOut])
def student_payments(student_id: int, db: DbSession, lang: Language, ctx: AuthContext = CanRead):
    s = StudentRepository(db).get_with_user(student_id, org_id=ctx.organization_id)
    if not s:
        raise HTTPException(404, t("common.not_found", lang))
    ensure_student_access(db, ctx, s)
    return PaymentService(db, ctx.organization_id).student_history(student_id)
