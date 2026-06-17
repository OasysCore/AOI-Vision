"""AOI-Vision v0.1 — 视觉分析引擎
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 目标计数 + 条码/二维码识别
"""
import cv2
import numpy as np
from typing import Optional

class VisionAnalyzer:
    """计数与条码"""

    @staticmethod
    def count_objects(frame: np.ndarray, min_area: int = 100, max_area: int = 100000,
                      threshold: int = 127, blur_ksize: int = 5) -> dict:
        """Blob检测计数"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
        _, binary = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        objects = []
        for c in contours:
            area = cv2.contourArea(c)
            if min_area <= area <= max_area:
                x, y, w, h = cv2.boundingRect(c)
                objects.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h), "area": int(area)})
        return {"count": len(objects), "objects": objects}

    @staticmethod
    def read_barcode(frame: np.ndarray) -> Optional[list[dict]]:
        """条码/二维码识别 (pyzbar)"""
        try:
            from pyzbar.pyzbar import decode
            results = decode(frame)
            return [{"data": r.data.decode("utf-8"), "type": r.type,
                     "rect": {"x": r.rect.left, "y": r.rect.top, "w": r.rect.width, "h": r.rect.height}}
                    for r in results] if results else None
        except ImportError:
            return None

    @staticmethod
    def measure_distance(p1: tuple, p2: tuple, pixels_per_mm: float) -> dict:
        """计算两点间实际距离"""
        pixel_dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        return {"pixel_distance": round(pixel_dist, 2), "real_mm": round(pixel_dist / pixels_per_mm, 3),
                "unit": "mm"}

    @staticmethod
    def measure_circle(frame: np.ndarray, center: tuple, radius: int, pixels_per_mm: float) -> dict:
        """测量圆形特征"""
        diameter_px = radius * 2
        circumference_px = 2 * np.pi * radius
        return {"diameter_px": round(diameter_px, 1), "diameter_mm": round(diameter_px / pixels_per_mm, 3),
                "circumference_mm": round(circumference_px / pixels_per_mm, 3), "radius_mm": round(radius / pixels_per_mm, 3)}
