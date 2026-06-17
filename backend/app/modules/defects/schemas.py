"""AOI-Vision v0.1 — 缺陷检测 schemas
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# --- DefectItem (embedded in InspectionResult) ---

class DefectItemSchema(BaseModel):
    type: str
    severity: str  # critical / major / minor
    x: int
    y: int
    w: int
    h: int
    area: float
    description: str


# --- InspectionRule CRUD ---

class RuleCreate(BaseModel):
    name: str
    type: str  # template_match / contour / color_threshold
    params: dict = {}
    golden_image_path: str | None = None
    threshold: float = 0.95
    is_active: bool = True


class RuleUpdate(BaseModel):
    name: str | None = None
    params: dict | None = None
    golden_image_path: str | None = None
    threshold: float | None = None
    is_active: bool | None = None


class RuleResponse(BaseModel):
    id: UUID
    name: str
    type: str
    params: dict
    golden_image_path: str | None
    threshold: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Inspection Request / Response ---

class InspectRequest(BaseModel):
    rule_id: UUID
    capture: bool = False  # whether to capture from camera live


class InspectUploadRequest(BaseModel):
    rule_id: UUID | None = None


class InspectionResultResponse(BaseModel):
    id: UUID
    rule_id: UUID
    image_path: str | None
    defect_count: int
    pass_fail: bool
    roi_regions: list
    defects: list
    confidence: float
    created_at: datetime
    created_by: UUID | None

    model_config = {"from_attributes": True}


class InspectionResultListResponse(BaseModel):
    items: list[InspectionResultResponse]
    total: int
    limit: int
    offset: int
