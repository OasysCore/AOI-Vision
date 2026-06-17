"""AOI-Vision v0.1
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 量测模块数据库模型 — 校准 + 量测记录
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func, JSON
from app.core.database import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Calibration(Base):
    __tablename__ = "calibrations"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    pixels_per_mm: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    records: Mapped[list["MeasurementRecord"]] = relationship(
        "MeasurementRecord", back_populates="calibration"
    )


class MeasurementRecord(Base):
    __tablename__ = "measurement_records"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    calibration_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("calibrations.id"), nullable=False
    )
    annotations: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    calibration: Mapped["Calibration"] = relationship(
        "Calibration", back_populates="records"
    )
