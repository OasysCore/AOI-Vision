# AOI-Vision 商业化架构文档

日期: 2026-06-17 | 作者: William Chao / OASYS CORE
版本: 0.2.0

---

## 一、三层架构

```
┌─────────────────────────────────────────────────┐
│                  UI Layer (展示层)                │
│  static/index.html — 纯 HTML/CSS/JS              │
│  零业务逻辑 • 零算法代码 • 仅 fetch + DOM 渲染      │
├─────────────────────────────────────────────────┤
│               Business Layer (业务层)             │
│  backend/app/ — FastAPI + SQLAlchemy             │
│  Auth / RBAC / CRUD / 报表 / 审计 / 设备管理       │
│  不含任何 OpenCV/numpy 算法代码                    │
├─────────────────────────────────────────────────┤
│              Core Engine (核心层)                 │
│  aoi_engine/ — 独立 Python 包                     │
│  所有 OpenCV 算法 • ModuleRegistry 模块选装        │
│  发布时 Cython 编译 .so — 不可逆，不可读            │
└─────────────────────────────────────────────────┘
```

## 二、核心层保护方案

1. **独立包**: `aoi_engine/` 不依赖 FastAPI/数据库/任何业务层模块
2. **Cython 编译**: `python setup.py build_ext --inplace` → `.so`
3. **发布时**: 删除 `.py` 源文件，只保留 `.so` + `setup.py`
4. **gRPC 通道**: 生产部署时业务层通过 gRPC 调用核心层（独立进程）

## 三、OpenCV 模块清单 (17个)

### 检测类 (Detection) — 6 模块

| 模块 | 技术 | 层级 | 适用场景 |
|------|------|------|---------|
| 模板比对 | 像素差 + 二值化 | Basic | 标准样品逐像素比对 |
| 轮廓分析 | Canny + findContours | Basic | 外形尺寸/边缘完整性 |
| 颜色阈值 | HSV 空间 + inRange | Basic | 特定颜色异常（污渍/氧化） |
| 特征匹配 | SIFT/ORB/AKAZE + BFMatcher | Advanced | 旋转/缩放不变目标定位 |
| 形态学顶帽 | tophat/blackhat 变换 | Advanced | 不均匀光照下的微小缺陷 |
| 频域分析 | DFT/FFT + 频域掩码 | Enterprise | 周期性纹理缺陷（PCB/屏幕） |

### 量测类 (Measurement) — 3 模块

| 模块 | 技术 | 层级 | 适用场景 |
|------|------|------|---------|
| 亚像素边缘 | cornerSubPix | Enterprise | μm 级精密量测 |
| 相机标定 | 棋盘格 + solvePnP | Enterprise | 镜头畸变校正+世界坐标 |
| 立体视觉 | StereoBM/SGBM | Enterprise | BGA焊点高度/3D尺寸 |

### 视觉增强 (Vision) — 8 模块

| 模块 | 技术 | 层级 | 适用场景 |
|------|------|------|---------|
| 图像配准 | ECC + findTransformECC | Advanced | 多相机对齐/抖动补偿 |
| 光流追踪 | Farneback/Lucas-Kanade | Advanced | 传送带物体追踪 |
| 超分辨率 | DNN 超分模型 | Enterprise | 低分辨率增强 |
| DNN 推理 | cv2.dnn + ONNX/TF | Enterprise | YOLO/MobileNet 端侧推理 |
| 目标计数 | Blob + findContours | Basic | 零件/焊点计数 |
| 条码识别 | pyzbar | Basic | 一维/二维码读取 |
| 全景拼接 | cv2.Stitcher | Enterprise | 大尺寸工件多图拼接 |
| 分水岭分割 | watershed | Advanced | 粘连物体分离 |

### 依赖关系

```
camera_calibration ← subpixel_edge
stereo_vision      ← camera_calibration
super_resolution   ← template_match
```

## 四、模块选装机制

SysAdmin 通过 API 或 UI 按客户需求选择启用哪些模块：

```
GET  /admin/engine-modules          → 查看所有模块及状态
POST /admin/engine-modules/{key}    → 启用/禁用模块 (body: {"enabled": true/false})
GET  /admin/engine-modules/config   → 导出当前配置快照
```

**典型客户套餐:**

| 套餐 | 启用的模块 | 定价逻辑 |
|------|-----------|---------|
| 基础版 | template_match + contour_analysis + color_threshold + object_counting | 4 模块，快速入门 |
| 专业版 | + feature_match + morphology_tophat + image_registration + barcode_reader | 8 模块，多数产线 |
| 企业版 | 全部 17 模块 | 全功能 |

## 五、OpenCV 技术优势

- **C++ 内核**: SIMD/NEON/OpenCL 硬件加速，单帧推理 <10ms
- **DNN 模块**: 原生加载 ONNX/TensorFlow/PyTorch 模型，无需额外推理框架
- **15 年工业验证**: 华为/大疆/海康/比亚迪产线级验证
- **无运行时依赖**: 编译后单文件部署
- **硬件适配**: Intel IPP / NVIDIA CUDA / ARM NEON 自动切换

## 六、项目结构

```
AOI-Vision/
├── aoi_engine/              ← Core Engine (独立包，Cython 编译候选)
│   ├── __init__.py          # 包入口，导出所有公共 API
│   ├── defect.py            # 缺陷检测引擎 (8种模式)
│   ├── vision.py            # 视觉分析 (计数+条码+量测)
│   ├── camera.py            # 相机抽象基类
│   ├── calibration.py       # 标定与量测
│   ├── registry.py          # 模块注册表 (17模块管理)
│   └── setup.py             # Cython 编译配置
├── backend/                 ← Business Layer
│   ├── app/
│   │   ├── main.py          # FastAPI 入口 + 路由注册
│   │   ├── core/            # 数据库/安全/配置
│   │   ├── modules/         # 业务模块 (auth/defects/measurement/...)
│   │   └── shared/          # 共享模型/工具
│   ├── static/index.html    # UI Layer (7标签页 + 4管理子标签)
│   ├── alembic/             # 数据库迁移
│   └── requirements.txt
├── docker-compose.yml
└── .gitignore
```

---

© 2026 潤芯國際(香港)有限公司 OASYS CORE INTERNATIONAL LIMITED
