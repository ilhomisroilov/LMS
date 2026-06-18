"""Payment schemas."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import PaymentStatus
from app.schemas.common import ORMModel


class PaymentCreate(BaseModel):
    student_id: int
    amount: float = Field(..., gt=0)
    amount_paid: float = 0
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$", examples=["2026-06"])


class PaymentUpdate(BaseModel):
    amount: float | None = None
    amount_paid: float | None = None
    status: PaymentStatus | None = None


class PaymentOut(ORMModel):
    id: int
    student_id: int
    student_name: str | None = None
    amount: float
    amount_paid: float
    month: str
    status: PaymentStatus
    created_at: datetime


class DashboardStats(BaseModel):
    total_students: int
    active_students: int
    total_teachers: int
    active_groups: int
    total_courses: int
    revenue_this_month: float | None = None
    debt_total: float | None = None
    attendance_rate: float  # % present over last 30 days
