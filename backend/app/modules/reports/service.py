"""AOI-Vision v0.1 — 报表模块
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: SPC 统计过程控制 + PDF 报告生成
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.defects.models import InspectionResult

async def get_spc_data(db: AsyncSession, days: int = 30) -> dict:
    """计算 CPK/PPK 控制图数据"""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(InspectionResult).where(InspectionResult.created_at >= since).order_by(InspectionResult.created_at)
    )
    records = result.scalars().all()

    if not records:
        return {"cpk": 0, "ppk": 0, "mean_defect_rate": 0, "sigma": 0, "samples": 0,
                "trend": [], "pass_rate": 100}

    defect_counts = [r.defect_count for r in records]
    n = len(defect_counts)
    mean = sum(defect_counts) / n
    variance = sum((x - mean) ** 2 for x in defect_counts) / (n - 1) if n > 1 else 0
    sigma = variance ** 0.5

    # CPK/PPK 简化计算（假设 USL = mean + 3*sigma, LSL = 0）
    usl = mean + 3 * sigma if sigma > 0 else mean + 1
    lsl = 0
    cpu = (usl - mean) / (3 * sigma) if sigma > 0 else 1.33
    cpl = (mean - lsl) / (3 * sigma) if sigma > 0 else 1.33
    cpk = min(cpu, cpl)
    ppk = cpk  # 简化处理

    pass_count = sum(1 for r in records if r.pass_fail)
    trend = [{"date": r.created_at.isoformat(), "defect_count": r.defect_count, "pass": r.pass_fail}
             for r in records]

    return {
        "cpk": round(cpk, 2),
        "ppk": round(ppk, 2),
        "mean_defect_rate": round(mean, 2),
        "sigma": round(sigma, 2),
        "samples": n,
        "pass_rate": round(pass_count / n * 100, 1),
        "trend": trend
    }

def generate_pdf_report(results: list[dict], spc_data: dict, output_path: str) -> str:
    """生成 PDF 检测报告"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm

        c = canvas.Canvas(output_path, pagesize=A4)
        w, h = A4

        c.setFont("Helvetica-Bold", 18)
        c.drawString(20 * mm, h - 20 * mm, "AOI-Vision 检测报告")

        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, h - 30 * mm, f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.drawString(20 * mm, h - 35 * mm, f"检测批次: {len(results)} 个 | 良率: {spc_data.get('pass_rate', 0)}%")
        c.drawString(20 * mm, h - 40 * mm, f"CPK: {spc_data.get('cpk', 0)} | 均值缺陷数: {spc_data.get('mean_defect_rate', 0)}")

        y = h - 55 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, "检测记录明细")
        y -= 8 * mm

        c.setFont("Helvetica", 8)
        for r in results[:50]:
            line = f"  {r.get('created_at', '')[:19]} | Defects: {r.get('defect_count', 0)} | {'PASS' if r.get('pass_fail') else 'FAIL'}"
            c.drawString(20 * mm, y, line)
            y -= 4 * mm
            if y < 20 * mm:
                c.showPage()
                y = h - 20 * mm

        c.setFont("Helvetica", 8)
        c.drawString(20 * mm, 15 * mm, "© 2026 潤芯國際(香港)有限公司 OASYS CORE — AOI-Vision 自动光学检测系统")
        c.save()
        return output_path
    except ImportError:
        return ""
