"""AOI-Vision v0.1 — 硬件抽象层
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 摄像头抽象接口 — 所有相机实现必须遵循此协议。
      换硬件只需新增一个子类，不改业务代码。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class CameraProperties:
    """相机属性快照"""
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    brightness: int = 128
    contrast: int = 128
    exposure: int = -1  # -1 = auto
    is_open: bool = False
    model_name: str = "unknown"


class BaseCamera(ABC):
    """摄像头抽象基类 — 所有相机驱动必须实现"""

    @abstractmethod
    def open(self, index: int = 0) -> bool:
        """打开摄像头，返回是否成功"""
        ...

    @abstractmethod
    def read_frame(self) -> Optional[np.ndarray]:
        """读取一帧 (BGR numpy array)，无帧返回 None"""
        ...

    @abstractmethod
    def release(self) -> None:
        """释放摄像头资源"""
        ...

    @abstractmethod
    def get_properties(self) -> CameraProperties:
        """获取当前相机属性"""
        ...

    def set_property(self, name: str, value: int) -> bool:
        """设置相机属性 (亮度/对比度/曝光)，返回是否成功。
           子类可选覆写。"""
        return False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.release()
