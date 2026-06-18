"""Shared enums used across models and schemas."""
import enum


class StudentStatus(str, enum.Enum):
    active = "active"
    frozen = "frozen"
    graduated = "graduated"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"


class PaymentStatus(str, enum.Enum):
    paid = "paid"
    unpaid = "unpaid"
    partial = "partial"


class LessonContentType(str, enum.Enum):
    text = "text"
    pdf = "pdf"
    video = "video"
