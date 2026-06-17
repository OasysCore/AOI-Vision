"""AOI-Vision v0.2 — RBAC schemas
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6)
    full_name: str = Field(default="", max_length=100)
    account_group_ids: list[str] = Field(default_factory=list)

class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=6)
    is_active: bool | None = None
    is_admin: bool | None = None
    account_group_ids: list[str] | None = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    is_admin: bool = False
    is_active: bool = True
    account_groups: list[dict] = Field(default_factory=list)
    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class AccountGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    permission_ids: list[str] = Field(default_factory=list)

class AccountGroupResponse(BaseModel):
    id: str
    name: str
    description: str
    is_active: bool
    permissions: list[dict] = Field(default_factory=list)
    model_config = {"from_attributes": True}

class PermissionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    permissions: dict = Field(default_factory=dict)

class PermissionResponse(BaseModel):
    id: str
    name: str
    description: str
    permissions: dict
    is_active: bool
    model_config = {"from_attributes": True}
