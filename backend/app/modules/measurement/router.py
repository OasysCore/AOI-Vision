"""AOI-Vision v0.1
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 量测模块路由 — 校准 & 量测记录 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.service import get_current_user
from app.modules.measurement import schemas
from app.modules.measurement import service

router = APIRouter(prefix="/measurement", tags=["Measurement"])


@router.post("/calibrate", response_model=schemas.CalibrateResponse)
async def calibrate(req: schemas.CalibrateRequest, user=Depends(get_current_user)):
    """根据像素距离和实际物理距离计算 pixels_per_mm"""
    ppm = service.calibrate_from_points(req.pixel_distance, req.real_mm)
    return schemas.CalibrateResponse(pixels_per_mm=ppm)


@router.get("/calibrations", response_model=list[schemas.CalibrationResponse])
async def get_calibrations(
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    """获取所有校准记录"""
    return await service.list_calibrations(db)


@router.post("/calibrations", response_model=schemas.CalibrationResponse, status_code=201)
async def create_calibration_route(
    req: schemas.CalibrationCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """创建校准记录"""
    return await service.create_calibration(db, req.name, req.pixels_per_mm)


@router.post("/records", response_model=schemas.MeasurementResponse, status_code=201)
async def create_record(
    req: schemas.MeasurementCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """保存量测记录"""
    cal = await service.get_calibration(db, req.calibration_id)
    if not cal:
        raise HTTPException(status_code=404, detail="Calibration not found")
    return await service.save_measurement(
        db, req.image_path, req.calibration_id, req.annotations
    )


@router.get("/records", response_model=list[schemas.MeasurementResponse])
async def get_records(
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    """获取所有量测记录"""
    return await service.list_measurements(db)
