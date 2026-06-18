"""Auth & token schemas."""
from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    phone: str = Field(..., examples=["+998901112233"])
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    phone: str
    password: str = Field(..., min_length=6)
    role: str = Field("student", description="admin | manager | teacher | student | parent")
    language: str = "uz"


class AcceptInviteRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class UserOut(ORMModel):
    id: int
    full_name: str
    phone: str
    is_active: bool
    language: str
    role_id: int


class LinkedEntities(BaseModel):
    """What the current user is connected to — drives parent/teacher scoping UI."""
    student_id: int | None = None
    teacher_id: int | None = None
    parent_id: int | None = None
    child_student_ids: list[int] = Field(default_factory=list)
    teacher_group_ids: list[int] = Field(default_factory=list)


class MeOut(UserOut):
    role: str
    organization_id: int
    branch_id: int | None = None
    must_change_password: bool = False
    permissions: list[str] = Field(default_factory=list)
    linked: LinkedEntities = Field(default_factory=LinkedEntities)
