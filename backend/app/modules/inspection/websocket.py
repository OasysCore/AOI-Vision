"""AOI-Vision v0.1
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 相机 WebSocket 端点 — 持续推送 JPEG 帧到前端。
"""
import asyncio
import time

from fastapi import APIRouter, WebSocket

from app.modules.inspection.camera_service import camera_manager

router = APIRouter()


@router.websocket("/ws/camera")
async def camera_websocket(ws: WebSocket):
    await ws.accept()
    started = camera_manager.start()
    if not started:
        await ws.send_json({"error": "Failed to start camera"})
        await ws.close()
        return

    try:
        frame_interval = 1.0 / 15  # 15 fps
        while camera_manager.is_running:
            b64 = camera_manager.encode_frame()
            if b64:
                try:
                    await ws.send_text(b64)
                except Exception:
                    break
            else:
                await ws.send_json({"info": "no frame"})
            await asyncio.sleep(frame_interval)
    finally:
        camera_manager.stop()
