"""AOI-Vision v0.1 — 管理模块 schemas
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from pydantic import BaseModel
from datetime import datetime

class FieldOptionCreate(BaseModel):
    field_name: str
    option_value: str
    option_label: str
    sort_order: int = 0

class FieldOptionUpdate(BaseModel):
    option_value: str | None = None
    option_label: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None

class FieldOptionResponse(BaseModel):
    id: int
    field_name: str
    option_value: str
    option_label: str
    sort_order: int
    is_active: bool
    model_config = {"from_attributes": True}

class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    username: str
    action: str
    entity_type: str
    entity_label: str | None = None
    summary: str | None = None
    model_config = {"from_attributes": True}

class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int
