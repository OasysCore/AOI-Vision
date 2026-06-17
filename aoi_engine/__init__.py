"""AOI Engine — 视觉核心引擎 (独立包)
========================================
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 所有 OpenCV 算法在此包内，与业务层/UI层零耦合。
      可独立于 FastAPI 运行。SysAdmin 可通过 ModuleRegistry 按客户需求打包。
      发布时用 Cython 编译为 .so，保护核心算法。

商业化三层架构:
  UI Layer (index.html)  ←HTTP→  Business Layer (FastAPI)  ←import→  Core Engine (aoi_engine)
"""
from aoi_engine.registry import ModuleRegistry, EngineModule, registry
from aoi_engine.defect import DefectEngine, InspectionResult, Defect
from aoi_engine.vision import VisionAnalyzer
from aoi_engine.camera import BaseCamera, CameraProperties
from aoi_engine.calibration import CalibrationEngine

__all__ = [
    "DefectEngine", "VisionAnalyzer", "BaseCamera", "CameraProperties", "CalibrationEngine",
    "ModuleRegistry", "EngineModule", "registry",
    "InspectionResult", "Defect",
]
__version__ = "0.2.0"
