"""AOI-Vision v0.1 — 审计日志模型
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: ERPNext 风格审计 — CUD 操作全记录
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text, func
from app.core.database import GUID
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.config import settings
from app.core.database import Base

# SQLite 用 JSON，PostgreSQL 用 JSONB
JSONType = SQLiteJSON if "sqlite" in settings.DATABASE_URL else __import__("sqlalchemy.dialects.postgresql", fromlist=["JSONB"]).JSONB

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    action: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    changes: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
