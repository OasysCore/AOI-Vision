"""AOI-Vision v0.1 — 报表 schemas + router
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.service import get_current_user
from app.modules.reports.service import get_spc_data, generate_pdf_report

router = APIRouter(prefix="/reports", tags=["Reports"])

class SPCTrendPoint(BaseModel):
    date: str
    defect_count: int
    pass_field: bool = True
    model_config = {"populate_by_name": True}


class SPCResponse(BaseModel):
    cpk: float
    ppk: float
    mean_defect_rate: float
    sigma: float
    samples: int
    pass_rate: float
    trend: list[dict]

@router.get("/spc", response_model=SPCResponse)
async def spc_data(days: int = Query(30, ge=7, le=365),
                   db: AsyncSession = Depends(get_db),
                   _user=Depends(get_current_user)):
    return await get_spc_data(db, days)

@router.get("/pdf")
async def download_pdf(db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    spc = await get_spc_data(db, 30)
    path = generate_pdf_report(spc.get("trend", []), spc, "/tmp/aoi_report.pdf")
    if not path:
        return {"error": "reportlab not installed"}
    return FileResponse(path, media_type="application/pdf", filename="AOI-Vision-Report.pdf")
