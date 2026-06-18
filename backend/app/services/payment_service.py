from __future__ import annotations
"""Payment & debt tracking."""
from sqlalchemy.orm import Session

from app.models.enums import PaymentStatus
from app.models.payment import Payment
from app.models.student import Student
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentUpdate
from app.services.exceptions import NotFoundError


class PaymentService:
    def __init__(self, db: Session, org_id: int | None = None) -> None:
        self.db = db
        self.org_id = org_id
        self.repo = PaymentRepository(db)

    @staticmethod
    def _derive_status(amount: float, paid: float) -> PaymentStatus:
        if paid <= 0:
            return PaymentStatus.unpaid
        if paid >= amount:
            return PaymentStatus.paid
        return PaymentStatus.partial

    @staticmethod
    def _to_out(p: Payment) -> PaymentOut:
        return PaymentOut(
            id=p.id, student_id=p.student_id,
            student_name=p.student.user.full_name if p.student and p.student.user else None,
            amount=float(p.amount), amount_paid=float(p.amount_paid),
            month=p.month, status=p.status, created_at=p.created_at,
        )

    def list(self, *, student_id=None, status=None, month=None, page=1, size=20):
        skip = (page - 1) * size
        rows, total = self.repo.list_full(
            student_id=student_id, status=status, month=month, skip=skip, limit=size,
            org_id=self.org_id,
        )
        return [self._to_out(p) for p in rows], total

    def create(self, data: PaymentCreate) -> PaymentOut:
        self._ensure_student(data.student_id)
        status = self._derive_status(data.amount, data.amount_paid)
        p = Payment(
            student_id=data.student_id, organization_id=self.org_id, amount=data.amount,
            amount_paid=data.amount_paid, month=data.month, status=status,
        )
        self.repo.add(p)
        self.db.commit()
        return self.get(p.id)

    def update(self, payment_id: int, data: PaymentUpdate) -> PaymentOut:
        p = self._get_payment(payment_id)
        if not p:
            raise NotFoundError()
        if data.amount is not None:
            p.amount = data.amount
        if data.amount_paid is not None:
            p.amount_paid = data.amount_paid
        p.status = data.status or self._derive_status(float(p.amount), float(p.amount_paid))
        self.db.commit()
        return self.get(payment_id)

    def get(self, payment_id: int) -> PaymentOut:
        p = self._get_payment(payment_id)
        if not p:
            raise NotFoundError()
        return self._to_out(p)

    def student_history(self, student_id: int) -> list[PaymentOut]:
        return [self._to_out(p) for p in self.repo.for_student(student_id)]

    def _ensure_student(self, student_id: int) -> None:
        student = self.db.get(Student, student_id)
        if not student or (self.org_id is not None and student.organization_id != self.org_id):
            raise NotFoundError()

    def _get_payment(self, payment_id: int) -> Payment | None:
        p = self.repo.get(payment_id)
        if p and self.org_id is not None and p.organization_id != self.org_id:
            return None
        return p
