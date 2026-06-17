"""AOI-Vision v0.2 — RBAC 权限模型
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 全多对多 RBAC — 权限组 ↔ 账号组 ↔ 用户
      Permission Group (权限组) ←M2M→ Account Group (账号组) ←M2M→ User (用户)
"""
import uuid
from sqlalchemy import Boolean, ForeignKey, String, Table, Column, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, GUID
from app.shared.models import TimestampMixin

# ====== M2M 关联表 ======

user_account_groups = Table(
    "user_account_groups", Base.metadata,
    Column("user_id", GUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("account_group_id", GUID, ForeignKey("account_groups.id", ondelete="CASCADE"), primary_key=True),
)

account_group_permissions = Table(
    "account_group_permissions", Base.metadata,
    Column("account_group_id", GUID, ForeignKey("account_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", GUID, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


# ====== 权限组 ======

class Permission(Base):
    """权限组 — 定义一组操作权限"""
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    # permissions dict: {"inspection":"manage","measurement":"read","defects":"manage",...}
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    account_groups: Mapped[list["AccountGroup"]] = relationship(
        "AccountGroup", secondary=account_group_permissions, back_populates="permissions"
    )


# ====== 账号组 ======

class AccountGroup(Base):
    """账号组 — 用户逻辑分组（如：质检员组、管理员组、操作员组）"""
    __tablename__ = "account_groups"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    users: Mapped[list["User"]] = relationship(
        "User", secondary=user_account_groups, back_populates="account_groups"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary=account_group_permissions, back_populates="account_groups"
    )


# ====== 用户 ======

class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), default="")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    account_groups: Mapped[list["AccountGroup"]] = relationship(
        "AccountGroup", secondary=user_account_groups, back_populates="users"
    )
