"""AOI-Vision v0.1
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 相机管理器 — 单例模式，后台线程采集最新帧，供 WebSocket 推送。
"""
import base64
import threading
import time
from typing import Optional

import cv2
import numpy as np

from app.core.config import settings
from app.hardware.factory import create_camera
from app.hardware.camera import BaseCamera


class CameraManager:
    """单例相机管理器 — 后台线程持续采集帧，暴露 get_frame / encode_frame。"""

    _instance: Optional["CameraManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CameraManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._camera: Optional[BaseCamera] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frame: Optional[np.ndarray] = None
        self._timestamp: Optional[float] = None
        self._buffer_lock = threading.Lock()
        self._target_fps = 15
        self._frame_interval = 1.0 / self._target_fps

    def start(self) -> bool:
        """启动相机采集线程。如果已经在运行则返回 True。"""
        if self._running:
            return True
        try:
            self._camera = create_camera(settings.CAMERA_TYPE, index=settings.CAMERA_INDEX)
            if not self._camera.open():
                return False
        except Exception:
            return False
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        """停止采集线程并释放相机。"""
        self._running = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        if self._camera is not None:
            self._camera.release()
            self._camera = None
        self._thread = None
        with self._buffer_lock:
            self._frame = None
            self._timestamp = None

    @property
    def is_running(self) -> bool:
        return self._running

    def _capture_loop(self) -> None:
        """后台采集循环，按目标帧率读取最新帧。"""
        while self._running:
            loop_start = time.time()
            if self._camera is not None:
                frame = self._camera.read_frame()
                if frame is not None:
                    with self._buffer_lock:
                        self._frame = frame
                        self._timestamp = time.time()
            elapsed = time.time() - loop_start
            sleep_time = max(0, self._frame_interval - elapsed)
            time.sleep(sleep_time)

    def get_frame(self) -> tuple[Optional[np.ndarray], Optional[float]]:
        """返回 (frame_bgr, timestamp) 或 (None, None)。"""
        with self._buffer_lock:
            if self._frame is None:
                return None, None
            return self._frame.copy(), self._timestamp

    def encode_frame(self, quality: int = 70) -> Optional[str]:
        """将当前帧编码为 base64 JPEG 字符串，用于 WebSocket 传输。"""
        frame, _ = self.get_frame()
        if frame is None:
            return None
        success, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not success:
            return None
        return base64.b64encode(encoded.tobytes()).decode("ascii")


# 模块级单例
camera_manager = CameraManager()
