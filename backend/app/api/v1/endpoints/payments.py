"""Payment / finance endpoints (admin manages)."""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.authz import AuthContext, require_permission
from app.core.deps import DbSession, Language
from app.core.i18n import t
from app.core.permissions import Perm
from app.schemas.common import Page
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentUpdate
from app.services.exceptions import ServiceError
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])
CanRead = Depends(require_permission(Perm.PAYMENT_READ))
CanWrite = Depends(require_permission(Perm.PAYMENT_WRITE))


@router.get("", response_model=Page[PaymentOut])
def list_payments(db: DbSession, student_id: int | None = None, status: str | None = None,
                  month: str | None = None, page: int = 1, size: int = Query(20, le=100),
                  ctx: AuthContext = CanRead):
    items, total = PaymentService(db, ctx.organization_id).list(
        student_id=student_id, status=status, month=month, page=page, size=size
    )
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=PaymentOut, status_code=201)
def create_payment(data: PaymentCreate, db: DbSession, ctx: AuthContext = CanWrite):
    return PaymentService(db, ctx.organization_id).create(data)


@router.patch("/{payment_id}", response_model=PaymentOut)
def update_payment(payment_id: int, data: PaymentUpdate, db: DbSession, lang: Language,
                   ctx: AuthContext = CanWrite):
    try:
        return PaymentService(db, ctx.organization_id).update(payment_id, data)
    except ServiceError as e:
        raise HTTPException(e.status_code, t(e.msg_key, lang))
