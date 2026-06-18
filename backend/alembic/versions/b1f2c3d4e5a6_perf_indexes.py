"""perf: add created_at indexes on payments and attendance

Revision ID: b1f2c3d4e5a6
Revises: 99a53ed7503a
Create Date: 2026-06-17

Adds indexes on payments.created_at and attendance.created_at to speed up
date-ordered/range queries (finance history, recent attendance). Other
frequently-filtered columns (users.phone, users.role_id, students.user_id,
teachers.user_id, groups.course_id, payments.student_id, attendance.student_id,
payments.month/status, attendance.lesson_date) are already indexed in the
initial schema.
"""
from alembic import op

revision = "b1f2c3d4e5a6"
down_revision = "99a53ed7503a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_payments_created_at", "payments", ["created_at"])
    op.create_index("ix_attendance_created_at", "attendance", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_attendance_created_at", table_name="attendance")
    op.drop_index("ix_payments_created_at", table_name="payments")
