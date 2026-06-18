"""Payment data access & finance aggregates."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import PaymentStatus
from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session) -> None:
        super().__init__(Payment, db)

    def list_full(self, *, student_id: int | None, status: str | None, month: str | None,
                  skip: int, limit: int, org_id: int | None = None) -> tuple[list[Payment], int]:
        stmt = select(Payment).options(joinedload(Payment.student).joinedload(
            __import__("app.models.student", fromlist=["Student"]).Student.user
        ))
        if org_id is not None:
            stmt = stmt.where(Payment.organization_id == org_id)
        if student_id:
            stmt = stmt.where(Payment.student_id == student_id)
        if status:
            stmt = stmt.where(Payment.status == status)
        if month:
            stmt = stmt.where(Payment.month == month)
        total = self.db.scalar(
            select(func.count()).select_from(stmt.order_by(None).subquery())
        ) or 0
        rows = list(self.db.scalars(
            stmt.order_by(Payment.month.desc()).offset(skip).limit(limit)
        ).unique().all())
        return rows, total

    def for_student(self, student_id: int) -> list[Payment]:
        return list(self.db.scalars(
            select(Payment).where(Payment.student_id == student_id).order_by(Payment.month.desc())
        ).all())

    def revenue_for_month(self, month: str, org_id: int | None = None) -> float:
        stmt = select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(Payment.month == month)
        if org_id is not None:
            stmt = stmt.where(Payment.organization_id == org_id)
        return float(self.db.scalar(stmt) or 0)

    def total_debt(self, org_id: int | None = None) -> float:
        stmt = select(func.coalesce(func.sum(Payment.amount - Payment.amount_paid), 0)).where(
            Payment.status != PaymentStatus.paid
        )
        if org_id is not None:
            stmt = stmt.where(Payment.organization_id == org_id)
        return float(self.db.scalar(stmt) or 0)

    @staticmethod
    def current_month() -> str:
        return date.today().strftime("%Y-%m")
