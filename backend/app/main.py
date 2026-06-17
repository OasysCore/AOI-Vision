"""AOI-Vision v0.1 — 自动光学检测系统
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: FastAPI 应用入口，路由注册
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.auth import router as auth_router
from app.modules.admin import router as admin_router, seed_default_options
from app.modules.defects import router as defects_router
from app.modules.measurement import router as measurement_router
from app.modules.reports import router as reports_router
from app.modules.device_router import router as device_router
from app.modules.inspection.websocket import router as ws_router

app = FastAPI(title="AOI-Vision", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(defects_router)
app.include_router(measurement_router)
app.include_router(reports_router)
app.include_router(device_router)
app.include_router(ws_router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
