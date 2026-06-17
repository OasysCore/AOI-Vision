"""AOI-Vision v0.1 — 认证模块 schemas
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6)
    full_name: str = Field(default="", max_length=100)
    group_id: str | None = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    is_admin: bool = False
    group_id: str | None = None
    is_active: bool = True

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    permissions: dict = Field(default_factory=lambda: {
        "inspection": "read",
        "measurement": "read",
        "defects": "read",
        "reports": "read",
        "admin": "none"
    })

class GroupResponse(BaseModel):
    id: str
    name: str
    permissions: dict
    model_config = {"from_attributes": True}
