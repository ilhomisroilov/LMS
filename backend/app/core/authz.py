"""Authorization engine (v1.2 spec §12.2) — layers 2 & 3.

    AuthContext         immutable per-request actor (id, org, role, perms)
    require_permission  FastAPI dependency: role-permission gate (layer 2)
    ensure_*_access     ownership-scope resolvers (layer 3)

Layer 1 (tenant) lives in the repositories, which always filter by
``ctx.organization_id``. All three layers must pass for access.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.permissions import Perm, permission_strings_for, permissions_for
from app.models.group import Group, GroupStudent
from app.models.student import Student
from app.models.user import User


@dataclass(frozen=True)
class AuthContext:
    user_id: int
    organization_id: int
    branch_id: int | None
    role: str
    permissions: frozenset[str] = field(default_factory=frozenset)
    user: User | None = None

    def has(self, perm: Perm | str) -> bool:
        value = perm.value if isinstance(perm, Perm) else perm
        return value in self.permissions

    @property
    def is_admin_level(self) -> bool:
        return self.role in {"super_admin", "admin", "manager"}


def get_auth_context(user: CurrentUser) -> AuthContext:
    """Build the request-scoped AuthContext from the authenticated user.

    Org/role come from the *user record* (authoritative), not just the token —
    defense in depth against a stale or tampered token claim.
    """
    return AuthContext(
        user_id=user.id,
        organization_id=user.organization_id,
        branch_id=user.branch_id,
        role=user.role.name,
        permissions=frozenset(permission_strings_for(user.role.name)),
        user=user,
    )


def _forbidden(detail: str = "You do not have access to this resource.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def require_permission(*perms: Perm):
    """Dependency factory: require ALL listed permissions (layer 2).

    Usage:
        @router.get(..., )
        def handler(ctx: AuthContext = Depends(require_permission(Perm.STUDENT_READ))):
    """
    needed = {p.value for p in perms}

    def _dep(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if not needed.issubset(ctx.permissions):
            raise _forbidden()
        return ctx

    return _dep


def require_role(*roles: str):
    """Dependency factory: require one of the given coarse roles."""
    allowed = set(roles)

    def _dep(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if ctx.role not in allowed:
            raise _forbidden()
        return ctx

    return _dep


# --------------------------------------------------------------------------
# Ownership-scope resolvers (layer 3) — "may THIS actor touch THIS row?"
# Every resolver first enforces same-tenant, then the relationship rule.
# --------------------------------------------------------------------------

def _teacher_can_see_student(db: Session, ctx: AuthContext, student: Student) -> bool:
    """True if the student is in any group assigned to this teacher."""
    teacher = ctx.user.teacher if ctx.user else None
    if teacher is None:
        return False
    q = (
        select(GroupStudent.id)
        .join(Group, Group.id == GroupStudent.group_id)
        .where(
            GroupStudent.student_id == student.id,
            Group.teacher_id == teacher.id,
        )
        .limit(1)
    )
    return db.scalar(q) is not None


def ensure_student_access(db: Session, ctx: AuthContext, student: Student) -> Student:
    """Raise 403 unless ctx may access this student (layer 1 + 3)."""
    if student is None or student.organization_id != ctx.organization_id:
        raise _forbidden()
    if ctx.role in {"super_admin", "admin", "manager"}:
        return student
    if ctx.role == "student":
        if ctx.user and student.user_id == ctx.user_id:
            return student
        raise _forbidden()
    if ctx.role == "parent":
        parent = ctx.user.parent if ctx.user else None
        if parent and any(c.id == student.id for c in parent.children):
            return student
        raise _forbidden()
    if ctx.role == "teacher":
        if _teacher_can_see_student(db, ctx, student):
            return student
        raise _forbidden()
    raise _forbidden()


def ensure_same_tenant(ctx: AuthContext, organization_id: int) -> None:
    """Generic layer-1 guard for any resource carrying organization_id."""
    if organization_id != ctx.organization_id:
        raise _forbidden()
