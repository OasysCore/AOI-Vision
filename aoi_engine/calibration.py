"""Core Engine: 标定与量测
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
import numpy as np

class CalibrationEngine:
    """像素标定 + 尺寸量测"""

    @staticmethod
    def calibrate(pixel_distance: float, real_mm: float) -> float:
        """从已知距离计算 pixels_per_mm"""
        if real_mm <= 0: return 0
        return pixel_distance / real_mm

    @staticmethod
    def measure(pixel_value: float, pixels_per_mm: float) -> dict:
        """像素值转真实尺寸"""
        if pixels_per_mm <= 0: return {"pixel": pixel_value, "real_mm": 0}
        return {"pixel": round(pixel_value, 2), "real_mm": round(pixel_value / pixels_per_mm, 4)}
