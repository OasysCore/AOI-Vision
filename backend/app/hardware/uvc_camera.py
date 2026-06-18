"""AOI-Vision v0.1 — UVC 相机驱动
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 通用 USB Video Class 摄像头实现。
      兼容龙仕显微镜摄像头及所有标准 UVC 设备。
"""
import cv2
import numpy as np
from typing import Optional
from app.hardware.camera import BaseCamera, CameraProperties


class UVCCamera(BaseCamera):
    """通用 USB 相机 — 基于 OasysCoreCV VideoCapture"""

    def __init__(self):
        self._cap: Optional[cv2.VideoCapture] = None
        self._props = CameraProperties(model_name="UVC Camera")

    def open(self, index: int = 0) -> bool:
        self._cap = cv2.VideoCapture(index)
        if not self._cap.isOpened():
            self._cap = None
            return False
        # 尝试读取实际参数
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self._cap.get(cv2.CAP_PROP_FPS)
        if w > 0 and h > 0:
            self._props.width = w
            self._props.height = h
        if fps > 0:
            self._props.fps = fps
        self._props.is_open = True
        return True

    def read_frame(self) -> Optional[np.ndarray]:
        if self._cap is None:
            return None
        ret, frame = self._cap.read()
        return frame if ret else None

    def release(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None
        self._props.is_open = False

    def get_properties(self) -> CameraProperties:
        return self._props

    def set_property(self, name: str, value: int) -> bool:
        if self._cap is None:
            return False
        prop_map = {
            "brightness": cv2.CAP_PROP_BRIGHTNESS,
            "contrast": cv2.CAP_PROP_CONTRAST,
            "exposure": cv2.CAP_PROP_EXPOSURE,
            "width": cv2.CAP_PROP_FRAME_WIDTH,
            "height": cv2.CAP_PROP_FRAME_HEIGHT,
        }
        prop_id = prop_map.get(name)
        if prop_id is None:
            return False
        self._cap.set(prop_id, value)
        return True
