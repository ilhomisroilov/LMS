"""Import all models so SQLAlchemy registers them on Base.metadata."""
from app.models.organization import Branch, Organization
from app.models.role import Role, RoleName
from app.models.user import User, UserStatus
from app.models.refresh_token import RefreshToken
from app.models.invite import Invite
from app.models.audit_log import AuditLog
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.models.student import Student
from app.models.course import Course
from app.models.group import Group, GroupStudent
from app.models.lesson import Lesson, LessonProgress
from app.models.attendance import Attendance
from app.models.payment import Payment
from app.models.enums import (
    StudentStatus,
    AttendanceStatus,
    PaymentStatus,
    LessonContentType,
)

__all__ = [
    "Organization", "Branch", "Role", "RoleName", "User", "UserStatus",
    "RefreshToken", "Invite", "AuditLog", "Teacher", "Parent", "Student",
    "Course", "Group", "GroupStudent", "Lesson", "LessonProgress",
    "Attendance", "Payment", "StudentStatus", "AttendanceStatus",
    "PaymentStatus", "LessonContentType",
]
