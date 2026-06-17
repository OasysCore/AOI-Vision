"""AOI-Vision v0.2 — 缺陷检测引擎 (Core Engine wrapper)
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 代理到独立 aoi_engine 包。生产环境替换为 Cython .so
"""
try:
    from aoi_engine.defect import DefectEngine, InspectionResult, Defect
except ImportError:
    # Fallback: embedded engine
    from ._engine_fallback import DefectEngine, InspectionResult, Defect
import io
from typing import Any

import cv2
import numpy as np


class DefectEngine:
    """OpenCV 缺陷检测引擎"""

    def compare_with_golden(
        self, test_frame: np.ndarray, golden_frame: np.ndarray, threshold: float = 0.95
    ) -> dict:
        """模板比对缺陷检测

        Args:
            test_frame:  待检测帧 (BGR)
            golden_frame: 金样帧 (BGR)
            threshold:   匹配阈值 (0-1)

        Returns:
            dict with defect_count, defects list, diff_image (base64-encoded)
        """
        test_gray = cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY)
        golden_gray = cv2.cvtColor(golden_frame, cv2.COLOR_BGR2GRAY)

        # 尺寸对齐
        if test_gray.shape != golden_gray.shape:
            golden_gray = cv2.resize(golden_gray, (test_gray.shape[1], test_gray.shape[0]))

        diff = cv2.absdiff(test_gray, golden_gray)
        _, binary = cv2.threshold(diff, int((1 - threshold) * 255), 255, cv2.THRESH_BINARY)

        # 形态学去噪
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        defect_count = 0
        defects = []
        total_area = test_gray.shape[0] * test_gray.shape[1]

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 10:  # 过滤极小噪点
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            severity = self._classify_by_area(area, total_area)
            defects.append(
                {
                    "type": "anomaly",
                    "severity": severity,
                    "x": int(x),
                    "y": int(y),
                    "w": int(w),
                    "h": int(h),
                    "area": float(area),
                    "description": f"差异区域 ({w}x{h}px, {area:.0f}px²)",
                }
            )
            defect_count += 1

        # 编码 diff 图像为 base64 PNG
        diff_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        _, buf = cv2.imencode(".png", diff_bgr)
        diff_b64 = buf.tobytes()

        return {
            "defect_count": defect_count,
            "defects": defects,
            "diff_image_bytes": diff_b64,
        }

    def detect_by_contour(self, frame: np.ndarray, params: dict | None = None) -> dict:
        """轮廓分析检测

        通过边缘检测 + 轮廓筛选发现异常几何形状。

        Args:
            frame:  输入帧 (BGR)
            params: 可选参数 {min_area, max_area, canny_low, canny_high, blur_ksize}

        Returns:
            dict with count, contours list
        """
        if params is None:
            params = {}

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur_ksize = params.get("blur_ksize", 5)
        blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)

        canny_low = params.get("canny_low", 50)
        canny_high = params.get("canny_high", 150)
        edges = cv2.Canny(blurred, canny_low, canny_high)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area = params.get("min_area", 100)
        max_area = params.get("max_area", 500000)

        contour_list = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            contour_list.append(
                {
                    "x": int(x),
                    "y": int(y),
                    "w": int(w),
                    "h": int(h),
                    "area": float(area),
                }
            )

        return {"count": len(contour_list), "contours": contour_list}

    def detect_by_color(self, frame: np.ndarray, params: dict | None = None) -> dict:
        """颜色阈值检测 (HSV)

        Args:
            frame:  输入帧 (BGR)
            params: {lower: [h, s, v], upper: [h, s, v], morph_kernel_size, min_area}

        Returns:
            dict with defect_count, defects list
        """
        if params is None:
            params = {}

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower = np.array(params.get("lower", [0, 50, 50]), dtype=np.uint8)
        upper = np.array(params.get("upper", [10, 255, 255]), dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)

        # 形态学开闭去噪
        ks = params.get("morph_kernel_size", 5)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ks, ks))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area = params.get("min_area", 20)
        total_area = frame.shape[0] * frame.shape[1]

        defect_count = 0
        defects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            severity = self._classify_by_area(area, total_area)
            defects.append(
                {
                    "type": "color_defect",
                    "severity": severity,
                    "x": int(x),
                    "y": int(y),
                    "w": int(w),
                    "h": int(h),
                    "area": float(area),
                    "description": f"颜色异常区域 ({w}x{h}px, {area:.0f}px²)",
                }
            )
            defect_count += 1

        return {"defect_count": defect_count, "defects": defects}

    def _classify_by_area(
        self, area: float, total_area: float, params: dict | None = None
    ) -> str:
        """根据面积占比分级：critical / major / minor"""
        if params is None:
            params = {}
        ratio = area / max(total_area, 1)
        critical_threshold = params.get("critical_area_ratio", 0.05)  # >5% → critical
        major_threshold = params.get("major_area_ratio", 0.01)       # >1% → major

        if ratio > critical_threshold:
            return "critical"
        elif ratio > major_threshold:
            return "major"
        else:
            return "minor"

    def run_inspection(
        self,
        frame: np.ndarray,
        rule_type: str,
        rule_params: dict,
        golden_frame: np.ndarray | None = None,
        threshold: float = 0.95,
    ) -> dict:
        """运行单个检测规则，返回统一的检测结果字典

        Returns:
            dict with defect_count, defects, pass_fail, confidence
        """
        result: dict[str, Any] = {
            "defect_count": 0,
            "defects": [],
            "pass_fail": True,
            "confidence": 0.0,
        }

        if rule_type == "template_match":
            if golden_frame is None:
                result["pass_fail"] = False
                result["defects"] = [
                    {
                        "type": "error",
                        "severity": "critical",
                        "x": 0,
                        "y": 0,
                        "w": 0,
                        "h": 0,
                        "area": 0,
                        "description": "模板比对模式需要 golden_frame",
                    }
                ]
                result["defect_count"] = 1
                return result
            out = self.compare_with_golden(frame, golden_frame, threshold)
            result["defect_count"] = out["defect_count"]
            result["defects"] = out["defects"]
        elif rule_type == "contour":
            out = self.detect_by_contour(frame, rule_params)
            # 每个轮廓视为一个缺陷
            defects = []
            for c in out["contours"]:
                defects.append(
                    {
                        "type": "contour_anomaly",
                        "severity": self._classify_by_area(
                            c["area"],
                            frame.shape[0] * frame.shape[1],
                            rule_params,
                        ),
                        "x": c["x"],
                        "y": c["y"],
                        "w": c["w"],
                        "h": c["h"],
                        "area": c["area"],
                        "description": f"轮廓异常 ({c['w']}x{c['h']}px)",
                    }
                )
            result["defect_count"] = out["count"]
            result["defects"] = defects
        elif rule_type == "color_threshold":
            out = self.detect_by_color(frame, rule_params)
            result["defect_count"] = out["defect_count"]
            result["defects"] = out["defects"]
        else:
            result["defects"] = [
                {
                    "type": "error",
                    "severity": "critical",
                    "x": 0,
                    "y": 0,
                    "w": 0,
                    "h": 0,
                    "area": 0,
                    "description": f"未知检测类型: {rule_type}",
                }
            ]
            result["defect_count"] = 1

        # 判定 pass / fail
        max_allowed = rule_params.get("max_defects", 0)
        result["pass_fail"] = result["defect_count"] <= max_allowed

        # 置信度 (粗略估计：无缺陷 → 高置信，有缺陷 → 中等置信)
        if result["defect_count"] == 0:
            result["confidence"] = 0.99
        else:
            # 基于缺陷数量的简单置信度模型
            result["confidence"] = max(0.5, 1.0 - result["defect_count"] * 0.1)

        return result
