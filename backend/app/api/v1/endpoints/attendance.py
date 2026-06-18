"""Attendance endpoints (teachers mark; staff view)."""
from datetime import date

from fastapi import APIRouter, Depends

from app.core.authz import AuthContext, require_permission
from app.core.deps import DbSession
from app.core.permissions import Perm
from app.schemas.attendance import AttendanceBulkCreate, AttendanceOut
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["attendance"])
CanRead = Depends(require_permission(Perm.ATTENDANCE_READ))
CanWrite = Depends(require_permission(Perm.ATTENDANCE_WRITE))


@router.post("", response_model=list[AttendanceOut])
def mark_attendance(data: AttendanceBulkCreate, db: DbSession, ctx: AuthContext = CanWrite):
    return AttendanceService(db, ctx.organization_id).mark_bulk(data)


@router.get("/group/{group_id}", response_model=list[AttendanceOut])
def group_attendance(group_id: int, db: DbSession, lesson_date: date | None = None,
                     ctx: AuthContext = CanRead):
    return AttendanceService(db, ctx.organization_id).group_history(group_id, lesson_date)
