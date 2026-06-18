"""Role → permission matrix (v1.2 spec §2.3).

This is layer 2 of the three-layer authorization model:

    1. tenant scope        (organization_id match)        -> repositories
    2. role permission     (does the role hold the perm?) -> THIS MODULE
    3. ownership scope      (may this actor touch this row?) -> core.authz

Permissions are coarse strings ``<domain>:<action>``. Roles are coarse; finer
row-level differences are handled by ownership scope + scope grants, never by
inventing new roles.
"""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    manager = "manager"
    teacher = "teacher"
    student = "student"
    parent = "parent"


class Perm(str, Enum):
    # Platform / tenancy
    ORG_MANAGE = "org:manage"
    BRANCH_MANAGE = "branch:manage"
    USER_MANAGE = "user:manage"
    AUDIT_READ = "audit:read"
    SETTINGS_WRITE = "settings:write"

    # CRM / sales
    LEAD_READ = "lead:read"
    LEAD_WRITE = "lead:write"

    # People
    STUDENT_READ = "student:read"
    STUDENT_WRITE = "student:write"
    TEACHER_READ = "teacher:read"
    TEACHER_WRITE = "teacher:write"
    PARENT_READ = "parent:read"
    PARENT_WRITE = "parent:write"

    # Learning ops
    GROUP_READ = "group:read"
    GROUP_WRITE = "group:write"
    COURSE_READ = "course:read"
    COURSE_WRITE = "course:write"
    ATTENDANCE_READ = "attendance:read"
    ATTENDANCE_WRITE = "attendance:write"
    TEST_CREATE = "test:create"
    TEST_TAKE = "test:take"
    TEST_GRADE = "test:grade"

    # Finance
    PAYMENT_READ = "payment:read"
    PAYMENT_WRITE = "payment:write"

    # Reporting
    REPORT_READ = "report:read"
    ANALYTICS_READ = "analytics:read"

    # Comms
    NOTIFY_BROADCAST = "notify:broadcast"


# Full operational set shared by admin/manager (manager trimmed below).
_FULL_OPS: set[Perm] = {
    Perm.LEAD_READ, Perm.LEAD_WRITE,
    Perm.STUDENT_READ, Perm.STUDENT_WRITE,
    Perm.TEACHER_READ, Perm.TEACHER_WRITE,
    Perm.PARENT_READ, Perm.PARENT_WRITE,
    Perm.GROUP_READ, Perm.GROUP_WRITE,
    Perm.COURSE_READ, Perm.COURSE_WRITE,
    Perm.ATTENDANCE_READ, Perm.ATTENDANCE_WRITE,
    Perm.TEST_CREATE, Perm.TEST_GRADE,
    Perm.PAYMENT_READ, Perm.PAYMENT_WRITE,
    Perm.REPORT_READ, Perm.ANALYTICS_READ,
    Perm.NOTIFY_BROADCAST,
}

ROLE_PERMISSIONS: dict[Role, set[Perm]] = {
    # Super admin: everything (platform operator). Represented as the union.
    Role.super_admin: set(Perm),

    # Admin (org owner): full operational control + org config + audit + users.
    Role.admin: _FULL_OPS | {
        Perm.ORG_MANAGE, Perm.BRANCH_MANAGE, Perm.USER_MANAGE,
        Perm.AUDIT_READ, Perm.SETTINGS_WRITE,
    },

    # Manager: operations, minus org config / user management / org-wide audit.
    Role.manager: _FULL_OPS | {Perm.AUDIT_READ},

    # Teacher: own groups/students — teaching operations only. No finance.
    Role.teacher: {
        Perm.STUDENT_READ,
        Perm.GROUP_READ,
        Perm.COURSE_READ,
        Perm.ATTENDANCE_READ, Perm.ATTENDANCE_WRITE,
        Perm.TEST_CREATE, Perm.TEST_GRADE,
        Perm.ANALYTICS_READ,
        Perm.NOTIFY_BROADCAST,
    },

    # Student: self only — take tests, read own data (enforced by ownership).
    Role.student: {
        Perm.TEST_TAKE,
    },

    # Parent: read linked children's data (enforced by ownership).
    Role.parent: set(),
}


def permissions_for(role: str | Role) -> set[Perm]:
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            return set()
    return ROLE_PERMISSIONS.get(role, set())


def role_has_permission(role: str | Role, perm: Perm) -> bool:
    return perm in permissions_for(role)


def permission_strings_for(role: str | Role) -> list[str]:
    """Sorted list of permission strings — used in the /me payload."""
    return sorted(p.value for p in permissions_for(role))
