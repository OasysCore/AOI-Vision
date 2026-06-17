"""AOI-Vision v0.1 — 设备网关路由
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 设备管理 API — HaaS506 遥测查看 + 远程控制
"""
from fastapi import APIRouter, Depends
from app.core.config import settings
from app.modules.auth.service import get_current_user
from app.hardware import create_device_gateway

router = APIRouter(prefix="/device", tags=["Device"])

@router.get("/telemetry")
async def device_telemetry(_user=Depends(get_current_user)):
    gw = create_device_gateway(settings.DEVICE_GATEWAY_TYPE)
    await gw.connect()
    try:
        telemetry = await gw.get_telemetry()
        return telemetry
    finally:
        await gw.disconnect()

@router.post("/relay")
async def set_relay(relay: int = 1, state: bool = False, _user=Depends(get_current_user)):
    from app.modules.auth.service import require_admin
    gw = create_device_gateway(settings.DEVICE_GATEWAY_TYPE)
    await gw.connect()
    try:
        result = await gw.send_command("set_relay", {"relay": relay, "state": state})
        return result
    finally:
        await gw.disconnect()
