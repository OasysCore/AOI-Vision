"""Core Engine: 缺陷检测
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 8 种 OasysCoreCV 检测模式，独立于业务层。
"""
import cv2
import numpy as np
from dataclasses import dataclass, field

@dataclass
class Defect:
    type: str = ""
    severity: str = "minor"  # critical / major / minor
    x: int = 0; y: int = 0; w: int = 0; h: int = 0
    area: int = 0; description: str = ""

@dataclass
class InspectionResult:
    rule_id: str = ""
    defect_count: int = 0
    pass_fail: bool = True
    defects: list[Defect] = field(default_factory=list)
    confidence: float = 1.0
    diff_image: np.ndarray | None = None

class DefectEngine:
    """AOI 缺陷检测引擎 — 8 种模式"""

    # === 模板比对 ===
    @staticmethod
    def template_match(test_frame: np.ndarray, golden_frame: np.ndarray, threshold: float = 0.95) -> InspectionResult:
        gray_t = cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY)
        gray_g = cv2.cvtColor(golden_frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray_t, gray_g)
        _, binary = cv2.threshold(diff, int((1 - threshold) * 255), 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        defects = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < 50: continue
            x, y, w, h = cv2.boundingRect(c)
            sev = "critical" if area > 5000 else "major" if area > 1000 else "minor"
            defects.append(Defect(type="diff", severity=sev, x=int(x), y=int(y), w=int(w), h=int(h), area=int(area), description=f"差异区域 ({int(area)}px²)"))
        return InspectionResult(defect_count=len(defects), pass_fail=len(defects) == 0, defects=defects, confidence=round(1 - len(defects) * 0.05, 2), diff_image=diff)

    # === 特征匹配 (SIFT/ORB) ===
    @staticmethod
    def feature_match(test_frame: np.ndarray, golden_frame: np.ndarray, min_matches: int = 10) -> InspectionResult:
        gray_t = cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY)
        gray_g = cv2.cvtColor(golden_frame, cv2.COLOR_BGR2GRAY)
        try: sift = cv2.SIFT_create()
        except: sift = cv2.ORB_create(500)
        kp1, des1 = sift.detectAndCompute(gray_g, None)
        kp2, des2 = sift.detectAndCompute(gray_t, None)
        if des1 is None or des2 is None:
            return InspectionResult(defect_count=0, pass_fail=True, confidence=0.0)
        bf = cv2.BFMatcher() if hasattr(cv2, 'SIFT_create') else cv2.BFMatcher(cv2.NORM_HAMMING)
        matches = bf.knnMatch(des1, des2, k=2)
        good = [m for m, n in matches if m.distance < 0.75 * n.distance]
        missing = max(0, len(kp1) - len(good))
        passed = len(good) >= min_matches
        defects = []
        if missing > 0:
            defects.append(Defect(type="feature_missing", severity="major" if missing > 5 else "minor", area=missing, description=f"缺失 {missing} 个特征点"))
        return InspectionResult(defect_count=len(defects), pass_fail=passed, defects=defects, confidence=round(len(good) / max(len(kp1), 1), 2))

    # === 频域缺陷检测 ===
    @staticmethod
    def frequency_domain(test_frame: np.ndarray, threshold: float = 0.1) -> InspectionResult:
        gray = cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        dft = cv2.dft(gray, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        magnitude = cv2.magnitude(dft_shift[:, :, 0], dft_shift[:, :, 1])
        mask = np.ones_like(magnitude)
        h, w = magnitude.shape
        cv2.circle(mask, (w // 2, h // 2), 30, 0, -1)  # 保留低频
        masked = magnitude * mask
        anomaly_mask = (masked > threshold).astype(np.uint8) * 255
        contours, _ = cv2.findContours(anomaly_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        defects = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < 20: continue
            x, y, w, h = cv2.boundingRect(c)
            defects.append(Defect(type="frequency_anomaly", severity="major", x=int(x), y=int(y), w=int(w), h=int(h), area=int(area), description=f"频域异常 ({int(area)}px²)"))
        return InspectionResult(defect_count=len(defects), pass_fail=len(defects) == 0, defects=defects, confidence=round(1 - len(defects) * 0.08, 2))

    # === 颜色阈值 (HSV) ===
    @staticmethod
    def color_threshold(test_frame: np.ndarray, lower: tuple, upper: tuple) -> InspectionResult:
        hsv = cv2.cvtColor(test_frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        defects = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < 30: continue
            x, y, w, h = cv2.boundingRect(c)
            defects.append(Defect(type="color_deviation", severity="major" if area > 2000 else "minor", x=int(x), y=int(y), w=int(w), h=int(h), area=int(area), description=f"色差区域 ({int(area)}px²)"))
        return InspectionResult(defect_count=len(defects), pass_fail=len(defects) == 0, defects=defects)

    # === 形态学 (顶帽变换) ===
    @staticmethod
    def morphology_tophat(test_frame: np.ndarray, kernel_size: int = 15) -> InspectionResult:
        gray = cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
        _, binary = cv2.threshold(tophat, 30, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        defects = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < 10: continue
            x, y, w, h = cv2.boundingRect(c)
            defects.append(Defect(type="tophat", severity="minor", x=int(x), y=int(y), w=int(w), h=int(h), area=int(area), description=f"微小凸起/划痕 ({int(area)}px²)"))
        return InspectionResult(defect_count=len(defects), pass_fail=len(defects) == 0, defects=defects)

    # === 轮廓分析 ===
    @staticmethod
    def contour_analysis(test_frame: np.ndarray, min_area: int = 100, max_area: int = 100000) -> InspectionResult:
        gray = cv2.cvtColor(test_frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        defects = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < min_area or area > max_area: continue
            x, y, w, h = cv2.boundingRect(c)
            defects.append(Defect(type="contour_anomaly", severity="minor", x=int(x), y=int(y), w=int(w), h=int(h), area=int(area), description=f"轮廓异常 ({int(area)}px²)"))
        return InspectionResult(defect_count=len(defects), pass_fail=len(defects) == 0, defects=defects)

    # === 边缘亚像素测量 ===
    @staticmethod
    def subpixel_edge(frame: np.ndarray, roi: tuple) -> list:
        x, y, w, h = roi
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        crop = gray[y:y + h, x:x + w]
        edges = cv2.Canny(crop, 50, 150)
        corners = cv2.goodFeaturesToTrack(edges, 50, 0.01, 10)
        if corners is None: return []
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        refined = cv2.cornerSubPix(crop, corners, (5, 5), (-1, -1), criteria)
        return [{"x": float(p[0][0]) + x, "y": float(p[0][1]) + y} for p in refined]

    # === 统一入口 ===
    @staticmethod
    def run(frame: np.ndarray, rule: dict, golden_frame: np.ndarray | None = None) -> InspectionResult:
        mode = rule.get("type", "template_match")
        params = rule.get("params", {})
        th = rule.get("threshold", 0.95)
        if mode == "template_match" and golden_frame is not None:
            return DefectEngine.template_match(frame, golden_frame, th)
        elif mode == "feature_match" and golden_frame is not None:
            return DefectEngine.feature_match(frame, golden_frame, params.get("min_matches", 10))
        elif mode == "frequency":
            return DefectEngine.frequency_domain(frame, th)
        elif mode == "color_threshold":
            lower = tuple(params.get("lower", [0, 0, 0]))
            upper = tuple(params.get("upper", [180, 255, 255]))
            return DefectEngine.color_threshold(frame, lower, upper)
        elif mode == "tophat":
            return DefectEngine.morphology_tophat(frame, params.get("kernel_size", 15))
        elif mode == "contour":
            return DefectEngine.contour_analysis(frame, params.get("min_area", 100), params.get("max_area", 100000))
        return DefectEngine.template_match(frame, golden_frame, th) if golden_frame is not None else InspectionResult()
