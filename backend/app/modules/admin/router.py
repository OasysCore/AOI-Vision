"""AOI-Vision v0.1 — 管理路由
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.service import get_current_user, require_permission
from app.modules.admin.schemas import FieldOptionCreate, FieldOptionUpdate, FieldOptionResponse, AuditLogListResponse
from app.modules.admin.service import list_options, create_option, update_option, delete_option, query_audit_logs

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/field-options", response_model=list[FieldOptionResponse])
async def get_options(field_name: str | None = Query(None), db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    return await list_options(db, field_name)

@router.post("/field-options", response_model=FieldOptionResponse)
async def add_option(data: FieldOptionCreate, db: AsyncSession = Depends(get_db), _admin=require_permission("admin", "manage")):
    return await create_option(db, data)

@router.put("/field-options/{opt_id}", response_model=FieldOptionResponse)
async def edit_option(opt_id: int, data: FieldOptionUpdate, db: AsyncSession = Depends(get_db), _admin=require_permission("admin", "manage")):
    opt = await update_option(db, opt_id, data)
    if not opt:
        from app.core.exceptions import AppException
        raise AppException(404, "Option not found")
    return opt

@router.delete("/field-options/{opt_id}", status_code=204)
async def remove_option(opt_id: int, db: AsyncSession = Depends(get_db), _admin=require_permission("admin", "manage")):
    ok = await delete_option(db, opt_id)
    if not ok:
        from app.core.exceptions import AppException
        raise AppException(404, "Option not found")

# ====== 模块管理 ======

@router.get("/engine-modules")
async def get_modules(_user=Depends(get_current_user)):
    """查看所有 OpenCV 模块及启用状态"""
    from aoi_engine import registry
    return registry.get_config()

@router.post("/engine-modules/{module_key}")
async def toggle_module(module_key: str, data: dict, _admin=require_permission("admin", "manage")):
    """启用/禁用指定模块"""
    from aoi_engine import registry
    enabled = data.get("enabled", True)
    ok = registry.toggle(module_key, enabled)
    return {"key": module_key, "enabled": registry.get(module_key).enabled if registry.get(module_key) else None, "success": ok}

@router.get("/engine-modules/config")
async def export_module_config(_user=Depends(get_current_user)):
    """导出当前模块配置快照（用于客户打包）"""
    from aoi_engine import registry
    return registry.get_config()

@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(entity_type: str | None = Query(None), action: str | None = Query(None),
                          username: str | None = Query(None), limit: int = Query(50, ge=1, le=200),
                          offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    items, total = await query_audit_logs(db, entity_type, action, username, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
