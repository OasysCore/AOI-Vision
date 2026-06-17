"""Core Engine: 相机抽象
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np

@dataclass
class CameraProperties:
    width: int = 1920; height: int = 1080; fps: float = 30.0
    brightness: int = 128; contrast: int = 128; exposure: int = -1
    is_open: bool = False; model_name: str = "unknown"

class BaseCamera(ABC):
    @abstractmethod
    def open(self, index: int = 0) -> bool: ...
    @abstractmethod
    def read_frame(self) -> np.ndarray | None: ...
    @abstractmethod
    def release(self) -> None: ...
    @abstractmethod
    def get_properties(self) -> CameraProperties: ...
    def set_property(self, name: str, value: int) -> bool: return False
    def __enter__(self): self.open(); return self
    def __exit__(self, *a): self.release()
