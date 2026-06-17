"""AOI-Vision v0.1 — 管理服务
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import FieldOption
from app.modules.admin.audit_model import AuditLog
from app.modules.admin.schemas import FieldOptionCreate, FieldOptionUpdate

async def list_options(db: AsyncSession, field_name: str | None = None) -> list[FieldOption]:
    stmt = select(FieldOption).where(FieldOption.is_active == True).order_by(FieldOption.sort_order)
    if field_name:
        stmt = stmt.where(FieldOption.field_name == field_name)
    return list((await db.execute(stmt)).scalars().all())

async def create_option(db: AsyncSession, data: FieldOptionCreate) -> FieldOption:
    opt = FieldOption(**data.model_dump())
    db.add(opt)
    await db.flush()
    return opt

async def update_option(db: AsyncSession, opt_id: int, data: FieldOptionUpdate) -> FieldOption | None:
    result = await db.execute(select(FieldOption).where(FieldOption.id == opt_id))
    opt = result.scalar_one_or_none()
    if not opt:
        return None
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(opt, key, val)
    await db.flush()
    return opt

async def delete_option(db: AsyncSession, opt_id: int) -> bool:
    result = await db.execute(select(FieldOption).where(FieldOption.id == opt_id))
    opt = result.scalar_one_or_none()
    if not opt:
        return False
    opt.is_active = False
    await db.flush()
    return True

async def seed_default_options(db: AsyncSession):
    """初始化默认枚举值"""
    defaults = [
        ("defect_type", "scratch", "划痕", 1),
        ("defect_type", "dent", "凹陷", 2),
        ("defect_type", "stain", "污渍", 3),
        ("defect_type", "crack", "裂纹", 4),
        ("defect_type", "burr", "毛刺", 5),
        ("defect_severity", "critical", "严重", 1),
        ("defect_severity", "major", "主要", 2),
        ("defect_severity", "minor", "次要", 3),
        ("product_model", "model-a", "产品A型", 1),
        ("product_model", "model-b", "产品B型", 2),
        ("production_line", "line-1", "产线1号", 1),
        ("production_line", "line-2", "产线2号", 2),
    ]
    for fn, ov, ol, so in defaults:
        existing = await db.execute(select(FieldOption).where(FieldOption.field_name == fn, FieldOption.option_value == ov))
        if not existing.scalar_one_or_none():
            db.add(FieldOption(field_name=fn, option_value=ov, option_label=ol, sort_order=so))
    await db.flush()

async def query_audit_logs(db: AsyncSession, entity_type: str | None = None, action: str | None = None,
                            username: str | None = None, limit: int = 50, offset: int = 0) -> tuple[list, int]:
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
        count_stmt = count_stmt.where(AuditLog.entity_type == entity_type)
    if action:
        stmt = stmt.where(AuditLog.action == action)
        count_stmt = count_stmt.where(AuditLog.action == action)
    if username:
        stmt = stmt.where(AuditLog.username == username)
        count_stmt = count_stmt.where(AuditLog.username == username)
    stmt = stmt.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit)
    items = list((await db.execute(stmt)).scalars().all())
    total = (await db.execute(count_stmt)).scalar() or 0
    return items, total
