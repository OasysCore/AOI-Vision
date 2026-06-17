"""AOI-Vision v0.1 — Mock 相机
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 无硬件时的模拟相机 — 用于开发测试/CI。
      支持纯色图、棋盘格、从图片文件读取。
"""
import cv2
import numpy as np
from typing import Optional
from app.hardware.camera import BaseCamera, CameraProperties


class MockCamera(BaseCamera):
    """模拟相机 — 无硬件依赖，用于开发和自动化测试"""

    MODE_SOLID = "solid"
    MODE_CHECKERBOARD = "checkerboard"
    MODE_FILE = "file"

    def __init__(self, mode: str = MODE_CHECKERBOARD,
                 width: int = 1920, height: int = 1080,
                 file_path: Optional[str] = None):
        self._mode = mode
        self._file_path = file_path
        self._frame_cache: Optional[np.ndarray] = None
        self._props = CameraProperties(
            width=width, height=height, fps=30,
            model_name=f"Mock Camera ({mode})"
        )

    def open(self, index: int = 0) -> bool:
        if self._mode == self.MODE_FILE and self._file_path:
            img = cv2.imread(self._file_path)
            if img is not None:
                self._frame_cache = cv2.resize(img, (self._props.width, self._props.height))
        if self._mode == self.MODE_SOLID:
            self._frame_cache = np.ones(
                (self._props.height, self._props.width, 3), dtype=np.uint8) * 128
        self._props.is_open = True
        return True

    def read_frame(self) -> Optional[np.ndarray]:
        if not self._props.is_open:
            return None
        if self._frame_cache is not None:
            return self._frame_cache.copy()
        # 动态生成棋盘格
        size = 100
        rows = self._props.height // size + 1
        cols = self._props.width // size + 1
        frame = np.zeros((self._props.height, self._props.width, 3), dtype=np.uint8)
        for r in range(rows):
            for c in range(cols):
                if (r + c) % 2 == 0:
                    y1, y2 = r * size, min((r + 1) * size, self._props.height)
                    x1, x2 = c * size, min((c + 1) * size, self._props.width)
                    frame[y1:y2, x1:x2] = 200
        return frame

    def release(self) -> None:
        self._props.is_open = False

    def get_properties(self) -> CameraProperties:
        return self._props
