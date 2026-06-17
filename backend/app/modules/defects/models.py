"""AOI-Vision v0.1 — 缺陷检测模型
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: InspectionRule + InspectionResult SQLAlchemy 模型
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models import TimestampMixin


class InspectionRule(TimestampMixin, Base):
    __tablename__ = "inspection_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # template_match / contour / color_threshold
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    golden_image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    threshold: Mapped[float] = mapped_column(Float, default=0.95)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    results: Mapped[list["InspectionResult"]] = relationship(
        "InspectionResult", back_populates="rule"
    )


class InspectionResult(TimestampMixin, Base):
    __tablename__ = "inspection_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspection_rules.id", ondelete="CASCADE"), nullable=False
    )
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    defect_count: Mapped[int] = mapped_column(Integer, default=0)
    pass_fail: Mapped[bool] = mapped_column(Boolean, default=True)  # True = pass
    roi_regions: Mapped[list] = mapped_column(JSON, default=list)
    defects: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    rule: Mapped["InspectionRule"] = relationship(
        "InspectionRule", back_populates="results"
    )
