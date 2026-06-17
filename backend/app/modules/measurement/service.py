"""AOI-Vision v0.1
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 量测模块服务层 — 校准与量测记录 CRUD
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.measurement.models import Calibration, MeasurementRecord


async def create_calibration(
    db: AsyncSession, name: str, pixels_per_mm: float
) -> Calibration:
    """创建校准记录"""
    cal = Calibration(name=name, pixels_per_mm=pixels_per_mm)
    db.add(cal)
    await db.flush()
    return cal


async def list_calibrations(db: AsyncSession) -> list[Calibration]:
    """列出所有校准记录"""
    result = await db.execute(
        select(Calibration).order_by(Calibration.created_at.desc())
    )
    return list(result.scalars().all())


async def get_calibration(db: AsyncSession, calibration_id: str) -> Calibration | None:
    """获取单个校准记录"""
    result = await db.execute(
        select(Calibration).where(Calibration.id == uuid.UUID(calibration_id))
    )
    return result.scalar_one_or_none()


def calibrate_from_points(pixel_distance: float, real_mm: float) -> float:
    """根据像素距离和实际物理距离计算像素-毫米比"""
    return pixel_distance / real_mm


async def save_measurement(
    db: AsyncSession, image_path: str, calibration_id: str, annotations: list
) -> MeasurementRecord:
    """保存量测记录"""
    record = MeasurementRecord(
        image_path=image_path,
        calibration_id=uuid.UUID(calibration_id),
        annotations=[a.model_dump() if hasattr(a, "model_dump") else a for a in annotations],
    )
    db.add(record)
    await db.flush()
    return record


async def list_measurements(db: AsyncSession) -> list[MeasurementRecord]:
    """列出所有量测记录"""
    result = await db.execute(
        select(MeasurementRecord).order_by(MeasurementRecord.created_at.desc())
    )
    return list(result.scalars().all())
