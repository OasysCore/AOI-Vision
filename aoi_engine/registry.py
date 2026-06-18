"""Core Engine: 模块注册表 — 管理所有 OasysCoreCV 模块的启用/禁用
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 零依赖纯 Python 注册表。业务层通过 API 控制开关。
      发布时 Cython 编译 .so — 即使服务器被黑也看不到算法逻辑。
"""
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class EngineModule:
    """单个检测模块定义"""
    key: str                          # 唯一标识 "template_match" / "sift_feature" ...
    name: str                         # 中文名 "模板比对"
    category: str                     # 分类: detection / measurement / vision / analysis
    description: str                  # 功能描述
    requires: list[str] = field(default_factory=list)  # 前置依赖模块
    enabled: bool = True              # 是否启用
    params: dict = field(default_factory=dict)  # 模块参数
    level: str = "basic"              # basic / advanced / enterprise


# ====== 全功能模块定义 ======
ALL_MODULES: list[EngineModule] = [
    # ── 检测类 (Detection) ──
    EngineModule(key="template_match", name="模板比对", category="detection",
        description="将待测图像与标准模板逐像素比对，检出差异区域。最简单最快的检测方式。",
        level="basic"),
    EngineModule(key="feature_match", name="特征匹配 (SIFT/ORB)", category="detection",
        description="SIFT/ORB/AKAZE 特征点匹配。旋转/缩放/光照不变，适合定位和缺陷检出。",
        level="advanced"),
    EngineModule(key="contour_analysis", name="轮廓分析", category="detection",
        description="Canny边缘检测+轮廓提取。检查产品外形尺寸/边缘完整性。",
        level="basic"),
    EngineModule(key="color_threshold", name="颜色阈值 (HSV)", category="detection",
        description="HSV色彩空间阈值分割。检出特定颜色区域的异常（污渍/氧化/漏印）。",
        level="basic"),
    EngineModule(key="frequency_domain", name="频域分析 (FFT)", category="detection",
        description="DFT/FFT 频域缺陷检测。周期性纹理缺陷（PCB线路/布料/屏幕像素）的最强手段，频域异常直接暴露。",
        level="enterprise"),
    EngineModule(key="morphology_tophat", name="形态学顶帽", category="detection",
        description="不均匀光照下的微小颗粒/划痕检出。比直接二值化对光照变化鲁棒得多。",
        level="advanced"),

    # ── 量测类 (Measurement) ──
    EngineModule(key="subpixel_edge", name="亚像素边缘定位", category="measurement",
        description="cornerSubPix 亚像素精度角点/边缘定位。μm级精密量测的核心技术。",
        level="enterprise"),
    EngineModule(key="camera_calibration", name="相机标定与畸变校正", category="measurement",
        description="棋盘格标定 → 内参矩阵 + 畸变系数 → 真实世界坐标换算。消除镜头畸变误差。",
        requires=["subpixel_edge"], level="enterprise"),
    EngineModule(key="stereo_vision", name="立体视觉 (Stereo)", category="measurement",
        description="双相机3D重建。BGA焊点高度/元器件共面度/3D尺寸测量。",
        requires=["camera_calibration"], level="enterprise"),

    # ── 视觉增强 (Vision) ──
    EngineModule(key="image_registration", name="图像配准 (ECC)", category="vision",
        description="ECC/单应性变换。多相机对齐、抖动补偿、多图叠加去噪。",
        level="advanced"),
    EngineModule(key="optical_flow", name="光流追踪", category="vision",
        description="Farneback/Lucas-Kanade。运动模糊补偿、传送带物体追踪、速度测量。",
        level="advanced"),
    EngineModule(key="super_resolution", name="超分辨率增强", category="vision",
        description="DNN超分模型。低分辨率图像增强细节。对微小缺陷检测有显著提升。",
        requires=["template_match"], level="enterprise"),

    # ── DNN 推理 ──
    EngineModule(key="dnn_inference", name="DNN 深度学习推理", category="vision",
        description="OasysCoreCV DNN 模块加载 ONNX/TensorFlow/PyTorch 模型。YOLO/MobileNet/ResNet 端侧推理。",
        level="enterprise"),
    EngineModule(key="object_counting", name="目标计数", category="vision",
        description="Blob分析+轮廓计数。零件计数、焊点计数、颗粒计数。",
        level="basic"),
    EngineModule(key="barcode_reader", name="条码/二维码识别", category="vision",
        description="pyzbar 一维码/二维码读取。产品追溯、批次管理。",
        level="basic"),

    # ── 拼接 ──
    EngineModule(key="image_stitching", name="全景拼接", category="vision",
        description="OasysCoreCV Stitcher。大尺寸PCB/晶圆多图拼接。超大工件检测必备。",
        level="enterprise"),
]


class ModuleRegistry:
    """OasysCoreCV 模块注册表 — 单例
    
    Usage:
      reg = ModuleRegistry()
      reg.enable("feature_match")   # 按客户需求启用
      reg.disable("stereo_vision")  # 按客户预算禁用
      reg.enabled_modules  # 获取当前启用的模块列表
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._modules: dict[str, EngineModule] = {}
            cls._instance._initialized = False
        return cls._instance

    def initialize(self, overrides: dict[str, bool] | None = None):
        """启动时调用，加载所有模块。overrides 可覆盖默认启用状态。"""
        self._modules = {m.key: m for m in ALL_MODULES}
        if overrides:
            for key, enabled in overrides.items():
                if key in self._modules:
                    self._modules[key].enabled = enabled
        self._initialized = True

    @property
    def all_modules(self) -> list[EngineModule]:
        return list(self._modules.values())

    @property
    def enabled_modules(self) -> list[EngineModule]:
        return [m for m in self._modules.values() if m.enabled]

    @property
    def enabled_keys(self) -> list[str]:
        return [m.key for m in self.enabled_modules]

    def get(self, key: str) -> EngineModule | None:
        return self._modules.get(key)

    def enable(self, key: str) -> bool:
        m = self._modules.get(key)
        if m:
            # Check dependencies
            for dep in m.requires:
                dep_module = self._modules.get(dep)
                if dep_module and not dep_module.enabled:
                    return False  # Dependency not satisfied
            m.enabled = True
            return True
        return False

    def disable(self, key: str) -> bool:
        m = self._modules.get(key)
        if m:
            m.enabled = False
            return True
        return False

    def toggle(self, key: str, enabled: bool) -> bool:
        return self.enable(key) if enabled else self.disable(key)

    def get_config(self) -> dict:
        """导出当前配置（可用于保存/恢复）"""
        return {
            "modules": {m.key: m.enabled for m in self.all_modules},
            "enabled_count": len(self.enabled_modules),
            "total_count": len(self.all_modules),
            "details": [
                {"key": m.key, "name": m.name, "category": m.category,
                 "enabled": m.enabled, "level": m.level} for m in self.all_modules
            ]
        }

    def to_dict(self) -> dict:
        return self.get_config()


# 全局单例
registry = ModuleRegistry()
registry.initialize()  # 默认全部启用
