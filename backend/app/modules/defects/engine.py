"""AOI-Vision v0.2 — 缺陷检测引擎 (Core Engine wrapper)
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 代理到独立 aoi_engine 包。生产环境替换为 Cython .so
"""
try:
    from aoi_engine.defect import DefectEngine, InspectionResult, Defect  # noqa: F401
except ImportError:
    import cv2, numpy as np, io, base64
    from dataclasses import dataclass, field
    from typing import Any

    @dataclass
    class Defect:
        type: str = ""; severity: str = "minor"; x: int = 0; y: int = 0; w: int = 0; h: int = 0
        area: int = 0; description: str = ""

    @dataclass
    class InspectionResult:
        rule_id: str = ""; defect_count: int = 0; pass_fail: bool = True
        defects: list[Defect] = field(default_factory=list); confidence: float = 1.0

    class DefectEngine:
        @staticmethod
        def template_match(test_frame, golden_frame, threshold=0.95):
            gray1 = cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(golden_frame, cv2.COLOR_BGR2GRAY)
            diff = cv2.absdiff(gray1, gray2)
            _, binary = cv2.threshold(diff, int((1-threshold)*255), 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            defects = []; defect_count = 0
            for c in contours:
                area = cv2.contourArea(c)
                if area < 30: continue
                x, y, w, h = cv2.boundingRect(c)
                sev = "critical" if area > 5000 else "major" if area > 1000 else "minor"
                defect_count += 1
                defects.append(Defect(type="diff", severity=sev, x=int(x), y=int(y), w=int(w), h=int(h), area=int(area), description=f"差异区域"))
            return InspectionResult(defect_count=defect_count, pass_fail=defect_count == 0, defects=defects, confidence=round(1 - defect_count * 0.05, 2))

        @staticmethod
        def contour_analysis(frame, min_area=100, max_area=100000):
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(cv2.GaussianBlur(gray, (5,5), 0), 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            defects = []; defect_count = 0
            for c in contours:
                area = cv2.contourArea(c)
                if area < min_area or area > max_area: continue
                x, y, w, h = cv2.boundingRect(c)
                defect_count += 1
                defects.append(Defect(type="contour", severity="minor", x=int(x), y=int(y), w=int(w), h=int(h), area=int(area), description=f"轮廓异常"))
            return InspectionResult(defect_count=defect_count, pass_fail=defect_count == 0, defects=defects)

        @staticmethod
        def color_threshold(frame, lower=(0,0,0), upper=(180,255,255)):
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, lower, upper)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            defects = []; defect_count = 0
            for c in contours:
                area = cv2.contourArea(c)
                if area < 30: continue
                x, y, w, h = cv2.boundingRect(c)
                defect_count += 1
                defects.append(Defect(type="color", severity="major" if area > 2000 else "minor", x=int(x), y=int(y), w=int(w), h=int(h), area=int(area), description=f"色差"))
            return InspectionResult(defect_count=defect_count, pass_fail=defect_count == 0, defects=defects)

        @staticmethod
        def classify_severity(area, max_area=100000):
            ratio = area / max(max_area, 1)
            return "critical" if ratio > 0.05 else "major" if ratio > 0.01 else "minor"

        @staticmethod
        def run(frame, rule, golden_frame=None):
            mode = rule.get("type", "template_match")
            th = rule.get("threshold", 0.95)
            params = rule.get("params", {})
            if mode == "template_match" and golden_frame is not None:
                return DefectEngine.template_match(frame, golden_frame, th)
            elif mode == "contour":
                return DefectEngine.contour_analysis(frame, params.get("min_area", 100), params.get("max_area", 100000))
            elif mode == "color_threshold":
                return DefectEngine.color_threshold(frame, tuple(params.get("lower", [0,0,0])), tuple(params.get("upper", [180,255,255])))
            elif golden_frame is not None:
                return DefectEngine.template_match(frame, golden_frame, th)
            return InspectionResult()
