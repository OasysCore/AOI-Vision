"""AOI-Vision v0.1 — 认证模块
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: User + UserGroup SQLAlchemy 模型
"""
import uuid
from sqlalchemy import Boolean, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.shared.models import TimestampMixin

class UserGroup(Base):
    __tablename__ = "user_groups"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)

    users: Mapped[list["User"]] = relationship("User", back_populates="group")

class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), default="")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    group_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user_groups.id", ondelete="SET NULL"), nullable=True)

    group: Mapped[UserGroup | None] = relationship("UserGroup", back_populates="users")
