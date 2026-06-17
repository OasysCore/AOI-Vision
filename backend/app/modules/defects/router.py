"""AOI-Vision v0.1 — 缺陷检测路由
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
import os
import uuid
from datetime import datetime, timezone

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppException
from app.modules.auth.service import get_current_user
from app.modules.auth.models import User
from app.modules.defects.schemas import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    InspectRequest,
    InspectionResultResponse,
    InspectionResultListResponse,
)
from app.modules.defects.service import (
    list_rules,
    get_rule,
    create_rule,
    update_rule,
    delete_rule,
    run_inspection,
    list_results,
)
from app.modules.defects.engine import DefectEngine

router = APIRouter(prefix="/defects", tags=["Defects"])

UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "defects")
os.makedirs(UPLOAD_DIR, exist_ok=True)

engine = DefectEngine()


# ─── Rule CRUD ─────────────────────────────────────────────

@router.post("/rules", response_model=RuleResponse, status_code=201)
async def create_inspection_rule(
    data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """创建检测规则"""
    return await create_rule(db, data)


@router.get("/rules", response_model=list[RuleResponse])
async def list_inspection_rules(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """获取检测规则列表"""
    return await list_rules(db)


@router.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_inspection_rule(
    rule_id: uuid.UUID,
    data: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """更新检测规则"""
    rule = await update_rule(db, rule_id, data)
    if not rule:
        raise AppException(404, "Rule not found")
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_inspection_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """删除检测规则（软删除）"""
    ok = await delete_rule(db, rule_id)
    if not ok:
        raise AppException(404, "Rule not found")


# ─── Inspection ────────────────────────────────────────────

@router.post("/inspect", response_model=InspectionResultResponse)
async def inspect_live(
    req: InspectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """从实时摄像头采集并检测 (capture=True) 或使用模拟帧"""
    if req.capture:
        from app.hardware.factory import create_camera

        cam = create_camera()
        cam.open()
        try:
            frame = cam.read_frame()
            if frame is None:
                raise AppException(400, "Camera failed to capture frame")
        finally:
            cam.release()
    else:
        # 模拟测试帧 (640×480 随机噪声)
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    try:
        result = await run_inspection(db, req.rule_id, frame, user_id=user.id)
    except ValueError as e:
        raise AppException(404, str(e))

    return result


@router.post("/inspect/upload", response_model=InspectionResultResponse)
async def inspect_upload(
    image: UploadFile = File(...),
    rule_id: uuid.UUID = Query(..., description="检测规则 ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """上传图像进行缺陷检测"""
    # 保存上传文件
    file_ext = os.path.splitext(image.filename or "image.png")[1] or ".png"
    stored_name = f"{uuid.uuid4().hex}{file_ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)

    contents = await image.read()
    with open(stored_path, "wb") as f:
        f.write(contents)

    # 解码图像
    np_arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise AppException(400, "Invalid image file")

    try:
        result = await run_inspection(
            db, rule_id, frame, user_id=user.id, image_path=stored_path
        )
    except ValueError as e:
        raise AppException(404, str(e))

    return result


@router.get("/results", response_model=InspectionResultListResponse)
async def list_inspection_results(
    rule_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """查询检测历史"""
    items, total = await list_results(db, limit, offset, rule_id)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
