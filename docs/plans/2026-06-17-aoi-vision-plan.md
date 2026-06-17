# AOI-Vision 实施计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 构建一套基于 Web 的自动化光学检测 (AOI) 系统，连接工业显微镜摄像头，通过 OpenCV 实现缺陷检测、计数、量测，含账号权限管理、参数枚举、审计日志等完整企业级功能。

**Architecture:** FastAPI 后端 + React/Vite 前端 + OpenCV 视觉引擎 + PostgreSQL 数据持久化 + HaaS506-HD3 设备网关（4G 遥测/远程控制）。

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0 async, OpenCV, PostgreSQL, React 18, Vite, TailwindCSS, Zustand, Canvas API

**Hardware:** 龙仕显微镜摄像头（UVC USB 协议）+ HaaS506-HD3（4G RTU 网关）

---

## 系统架构

```
┌──────────────────────────────────────────────────────┐
│                    前端 (React)                       │
│   Dashboard │ 检测画面 │ 缺陷列表 │ 量测 │ 报表 │ 管理  │
└──────────────────────┬───────────────────────────────┘
                       │ HTTP REST + WebSocket
┌──────────────────────┴───────────────────────────────┐
│              后端 (FastAPI)                           │
│  ┌──────────┬──────────┬──────────┬───────────────┐  │
│  │  Auth    │ Inspection│ Measur.  │  Device GW    │  │
│  │  JWT     │ OpenCV    │ 尺寸计算  │  HaaS506 遥测  │  │
│  │  账号组   │ 模板比对  │ 公差判定  │  4G 状态上报   │  │
│  └──────────┴──────────┴──────────┴───────────────┘  │
│  ┌──────────────────────────────────────────────────┐ │
│  │ PostgreSQL ← 检测记录/缺陷/账号/审计/参数枚举      │ │
│  └──────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
                       │
┌──────────────────────┴───────────────────────────────┐
│                  硬件层                               │
│  ┌──────────────────┐  ┌─────────────────────────┐   │
│  │ 龙仕显微镜摄像头    │  │ HaaS506-HD3 (4G RTU)    │   │
│  │ USB UVC 协议       │  │ 远程启停/状态监控/告警    │   │
│  │ 自动对焦/可调倍率   │  │ MQTT ← → 阿里云 IoT      │   │
│  └──────────────────┘  └─────────────────────────┘   │
└───────────────────────────────────────────────────────┘
```

---

## 完整功能清单

### 用户明确要求

| # | 功能 | 说明 |
|---|------|------|
| F1 | 缺陷检测（可自定义） | 用户可创建/编辑检测规则（模板比对、轮廓分析、颜色阈值等） |
| F2 | 计数 | ROI 区域内目标自动计数 |
| F3 | 量测尺寸 | 基于标定尺的精确尺寸测量（mm/μm） |
| F4 | 账号管理 | 用户名+密码，JWT 认证 |
| F5 | 账号组 | Admin / 质检员 / 操作员（不同权限） |
| F6 | 参数枚举 | 下拉选项可配置（缺陷类型/产品型号/产线等） |
| F7 | 检视 Log | 操作审计日志，按操作人/类型/时间筛选 |

### AOI 业界标配（自动补全）

| # | 功能 | 说明 |
|---|------|------|
| A1 | 黄金模板比对 | 标准样品图 vs 待检图，差异热图，自动标记缺陷区域 |
| A2 | 多 ROI 分区检测 | 一个视野内划分多个检测区域，各自独立配置规则 |
| A3 | 缺陷分类分级 | 严重/主要/次要三级，自动判定 pass/fail |
| A4 | SPC 统计过程控制 | CPK/PPK 趋势图，质量波动告警 |
| A5 | 校准管理 | 像素→物理尺寸转换标定，支持多点校准 |
| A6 | 条码/二维码读取 | 产品追溯，扫描后自动关联到检测批次 |
| A7 | PDF 检测报告 | 一键生成含缺陷图、量测数据、结论的正式报告 |
| A8 | 实时视频流 | WebSocket 推送摄像头画面到前端 Canvas |
| A9 | 曝光/对焦控制 | 摄像头参数远程调节（亮度/对比度/曝光） |
| A10 | 设备健康监控 | HaaS506 上报 4G 信号、设备温度、运行时长 |

---

## 实施任务

### Phase 0: 项目基础设施

#### Task 0.1: 初始化项目骨架

**Objective:** 创建 FastAPI + React 双端项目结构

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

**Step 1: 后端 FastAPI 骨架**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AOI-Vision", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aoi_vision"
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    UPLOAD_DIR: str = "./uploads"
    CAMERA_INDEX: int = 0  # OpenCV 摄像头索引

    class Config:
        env_file = ".env"

settings = Settings()
```

```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Step 2: 前端 Vite+React 骨架**

```json
// frontend/package.json
{
  "name": "aoi-vision-frontend",
  "private": true,
  "scripts": { "dev": "vite", "build": "tsc && vite build" },
  "dependencies": {
    "react": "^18.3", "react-dom": "^18.3", "react-router-dom": "^6",
    "zustand": "^4", "axios": "^1", "tailwindcss": "^3"
  },
  "devDependencies": {
    "@types/react": "^18.3", "typescript": "^5", "vite": "^5",
    "@vitejs/plugin-react": "^4"
  }
}
```

**Step 3: Verify**

Run: `cd backend && uvicorn app.main:app --port 8000`
Run: `cd frontend && npm install && npm run dev`
Expected: Backend /health returns 200, frontend shows React default page

**Step 4: Commit**

```bash
cd /Users/williamchao/Documents/OpenCode/Project/AOI-Vision
git init && git add -A && git commit -m "init: AOI-Vision project skeleton (FastAPI + React)"
```

---

#### Task 0.2: Docker Compose 开发环境

**Objective:** PostgreSQL + PgAdmin 本地一键启动

**Files:**
- Create: `docker-compose.yml`

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: aoi_vision
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
volumes:
  pgdata:
```

Run: `docker compose up -d`
Expected: `docker compose ps` shows postgres healthy

---

### Phase 1: 认证与权限

#### Task 1.1: User & UserGroup 模型

#### Task 1.2: JWT 认证（注册/登录/刷新）

#### Task 1.3: 账号组权限中间件

#### Task 1.4: 前端登录页 + AuthContext

---

### Phase 2: 参数枚举系统

#### Task 2.1: FieldOption 模型 + CRUD API

#### Task 2.2: 前端参数枚举管理页（Admin）

---

### Phase 3: 相机与视频流

#### Task 3.1: OpenCV 相机封装

#### Task 3.2: WebSocket 视频流推送

#### Task 3.3: 前端实时视频画面渲染

---

### Phase 4: 校准与量测

#### Task 4.1: 校准模型 + 标定 API

#### Task 4.2: 前端标定界面（选两点输入实际距离）

#### Task 4.3: 画布量测工具（线段/矩形/圆形标注）

---

### Phase 5: 缺陷检测引擎

#### Task 5.1: InspectionRule 模型 + CRUD

#### Task 5.2: OpenCV 模板比对引擎

#### Task 5.3: 多 ROI 分区检测

#### Task 5.4: 缺陷分类与分级

#### Task 5.5: 缺陷标注可视化（画框+标签）

---

### Phase 6: 计数与条码

#### Task 6.1: 目标计数算法（blob detection / contour counting）

#### Task 6.2: 条码/二维码读取（pyzbar）

---

### Phase 7: SPC 与报表

#### Task 7.1: InspectionRecord 数据聚合

#### Task 7.2: CPK/PPK 趋势计算

#### Task 7.3: PDF 报告生成（reportlab）

#### Task 7.4: 前端 SPC 图表（recharts）

---

### Phase 8: 审计日志

#### Task 8.1: AuditLog 模型 + 中间件

#### Task 8.2: 前端日志查看器

---

### Phase 9: HaaS506 设备网关

#### Task 9.1: 设备上线注册 API

#### Task 9.2: 遥测数据接收与存储

#### Task 9.3: 前端设备监控面板

---

### Phase 10: 集成测试 & 部署

#### Task 10.1: 全栈端到端测试

#### Task 10.2: Nginx 部署配置

---

## 实施原则

- **硬件抽象层**：`app/hardware/` — 工厂模式懒加载，换硬件只改 `.env` 中 `CAMERA_TYPE` / `DEVICE_GATEWAY_TYPE`
- **bite-sized tasks** 每任务 2-5 分钟
- **TDD** 先测试后实现
- **Frequent commits** 每任务完成后提交
- **Two-stage review** spec review → code review
- **先用 mock 再换真实硬件** 初期用 MockCamera/MockDevice, 上线切 UVC/HaaS506
