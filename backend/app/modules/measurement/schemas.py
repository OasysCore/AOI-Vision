"""AOI-Vision v0.1
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 量测模块 Pydantic schemas
"""
from pydantic import BaseModel, Field


class CalibrateRequest(BaseModel):
    pixel_distance: float = Field(gt=0, description="像素距离")
    real_mm: float = Field(gt=0, description="实际物理距离 (mm)")


class CalibrateResponse(BaseModel):
    pixels_per_mm: float


class CalibrationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    pixels_per_mm: float = Field(gt=0)


class CalibrationResponse(BaseModel):
    id: str
    name: str
    pixels_per_mm: float
    created_at: str

    model_config = {"from_attributes": True}


class AnnotationItem(BaseModel):
    type: str = Field(description="标注类型: line | rect | circle | point")
    x1: float
    y1: float
    x2: float = 0.0
    y2: float = 0.0
    value: float = 0.0
    unit: str = "mm"


class MeasurementCreate(BaseModel):
    image_path: str
    calibration_id: str
    annotations: list[AnnotationItem] = Field(default_factory=list)


class MeasurementResponse(BaseModel):
    id: str
    image_path: str
    calibration_id: str
    annotations: list
    created_at: str

    model_config = {"from_attributes": True}
