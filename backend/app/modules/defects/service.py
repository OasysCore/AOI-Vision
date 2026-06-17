"""AOI-Vision v0.1 — 缺陷检测服务
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
import os
import uuid
from datetime import datetime, timezone

import cv2
import numpy as np
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.defects.engine import DefectEngine
from app.modules.defects.models import InspectionRule, InspectionResult
from app.modules.defects.schemas import RuleCreate, RuleUpdate

engine = DefectEngine()


# ─── Rule CRUD ─────────────────────────────────────────────

async def list_rules(db: AsyncSession) -> list[InspectionRule]:
    stmt = (
        select(InspectionRule)
        .where(InspectionRule.is_active == True)
        .order_by(desc(InspectionRule.created_at))
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_rule(db: AsyncSession, rule_id: uuid.UUID) -> InspectionRule | None:
    result = await db.execute(select(InspectionRule).where(InspectionRule.id == rule_id))
    return result.scalar_one_or_none()


async def create_rule(db: AsyncSession, data: RuleCreate) -> InspectionRule:
    rule = InspectionRule(**data.model_dump())
    db.add(rule)
    await db.flush()
    return rule


async def update_rule(
    db: AsyncSession, rule_id: uuid.UUID, data: RuleUpdate
) -> InspectionRule | None:
    result = await db.execute(select(InspectionRule).where(InspectionRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return None
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(rule, key, val)
    await db.flush()
    return rule


async def delete_rule(db: AsyncSession, rule_id: uuid.UUID) -> bool:
    result = await db.execute(select(InspectionRule).where(InspectionRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        return False
    rule.is_active = False
    await db.flush()
    return True


# ─── Inspection ────────────────────────────────────────────

async def run_inspection(
    db: AsyncSession,
    rule_id: uuid.UUID,
    frame: np.ndarray,
    user_id: uuid.UUID | None = None,
    image_path: str | None = None,
) -> InspectionResult:
    """执行检测并保存结果到数据库"""
    result = await db.execute(select(InspectionRule).where(InspectionRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise ValueError(f"Rule not found: {rule_id}")

    # 加载金样图（如有）
    golden_frame = None
    if rule.golden_image_path and os.path.isfile(rule.golden_image_path):
        golden_frame = cv2.imread(rule.golden_image_path)

    inspection_output = engine.run_inspection(
        frame=frame,
        rule_type=rule.type,
        rule_params=rule.params,
        golden_frame=golden_frame,
        threshold=rule.threshold,
    )

    ins_result = InspectionResult(
        rule_id=rule_id,
        image_path=image_path,
        defect_count=inspection_output["defect_count"],
        pass_fail=inspection_output["pass_fail"],
        roi_regions=[],
        defects=inspection_output["defects"],
        confidence=inspection_output["confidence"],
        created_by=user_id,
    )
    db.add(ins_result)
    await db.flush()
    return ins_result


async def list_results(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    rule_id: uuid.UUID | None = None,
) -> tuple[list[InspectionResult], int]:
    stmt = select(InspectionResult)
    count_stmt = select(func.count()).select_from(InspectionResult)
    if rule_id:
        stmt = stmt.where(InspectionResult.rule_id == rule_id)
        count_stmt = count_stmt.where(InspectionResult.rule_id == rule_id)

    stmt = stmt.order_by(desc(InspectionResult.created_at)).offset(offset).limit(limit)
    items = list((await db.execute(stmt)).scalars().all())
    total = (await db.execute(count_stmt)).scalar() or 0
    return items, total
