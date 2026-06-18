# AOI-Vision 部署手册 v0.2

日期: 2026-06-17 | 作者: William Chao / OASYS CORE
文档版本: 1.0

---

## 一、环境要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | x86_64 双核 | x86_64 四核以上 |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 10 GB 可用 | 50 GB+ SSD |
| 相机 | USB UVC / IP Camera | 工业相机（Basler/海康） |
| 网络 | 100 Mbps | 1 Gbps |

### 1.2 软件要求

| 软件 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 运行环境 |
| pip | 24.0+ | 包管理 |
| Git | 2.40+ | 代码获取 |
| SQLite | 3.35+ | 本地开发数据库 |
| PostgreSQL | 14+ | 生产数据库（可选） |

### 1.3 操作系统

- macOS 14+（开发）
- Ubuntu 22.04+ / Debian 12+（生产）
- Windows Server 2022（需配置 WSL2 或 Docker）

---

## 二、安装部署

### 2.1 获取源码

```bash
git clone https://github.com/OasysCore/AOI-Vision.git
cd AOI-Vision/backend
```

![获取源码]
> **图片标识: deploy-clone** — git clone 命令执行截图。

### 2.2 创建虚拟环境

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

### 2.3 安装依赖

```bash
pip install -r requirements.txt
```

![安装依赖]
> **图片标识: deploy-pip-install** — pip install 命令执行截图，显示安装成功。

### 2.4 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# 数据库（本地开发用 SQLite，零依赖）
DATABASE_URL=sqlite+aiosqlite:///./aoi_vision.db

# JWT 密钥（生产环境务必更换）
JWT_SECRET_KEY=your-production-secret-key-min-32-chars

# 相机类型（mock = 模拟相机, uvc = USB相机）
CAMERA_TYPE=mock
CAMERA_INDEX=0

# 设备网关（mock = 模拟, haas506 = HaaS506-HD3）
DEVICE_GATEWAY_TYPE=mock

# HaaS506 MQTT 配置（使用真实设备时填写）
MQTT_BROKER=broker.emqx.io
MQTT_PORT=1883
MQTT_TOPIC=haas506/telemetry
```

![配置文件]
> **图片标识: deploy-env** — .env 配置文件截图。

### 2.5 启动服务

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

![启动成功]
> **图片标识: deploy-startup** — uvicorn 启动输出，显示 "Application startup complete"。

### 2.6 验证部署

```bash
curl http://localhost:8000/health
# 预期输出: {"status":"ok","version":"0.1.0"}
```

浏览器访问 `http://localhost:8000`，应看到登录页面。

![验证部署]
> **图片标识: deploy-verify** — 浏览器打开系统登录页面的截图。

---

## 三、生产环境部署

### 3.1 Docker Compose 部署

```bash
cd /path/to/AOI-Vision
docker-compose up -d
```

**docker-compose.yml 说明：**

| 服务 | 端口 | 说明 |
|------|------|------|
| backend | 8000 | FastAPI 应用 |
| postgres | 5432 | PostgreSQL 数据库（生产模式） |

### 3.2 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name aoi-vision.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";  # WebSocket 支持
    }
}
```

```bash
nginx -t && systemctl reload nginx
```

![Nginx配置]
> **图片标识: deploy-nginx** — Nginx 配置文件截图。

### 3.3 生产数据库切换

编辑 `.env`，将 SQLite 切换为 PostgreSQL：

```ini
DATABASE_URL=postgresql+asyncpg://aoi_user:your_password@localhost:5432/aoi_vision
```

重启服务：

```bash
systemctl restart aoi-vision
```

![数据库切换]
> **图片标识: deploy-postgres** — 数据库切换后的启动日志截图。

### 3.4 设置系统服务

创建 systemd 服务文件 `/etc/systemd/system/aoi-vision.service`：

```ini
[Unit]
Description=AOI-Vision Backend Service
After=network.target

[Service]
Type=simple
User=aoi
WorkingDirectory=/opt/aoi-vision/backend
ExecStart=/opt/aoi-vision/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable aoi-vision
systemctl start aoi-vision
systemctl status aoi-vision
```

![系统服务]
> **图片标识: deploy-systemd** — systemctl status 输出截图。

---

## 四、硬件连接

### 4.1 相机连接

| 相机类型 | 配置 | 接线方式 |
|---------|------|---------|
| USB UVC | CAMERA_TYPE=uvc | USB 直连 |
| IP Camera | 需扩展驱动 | RJ45 网线 |
| Mock | CAMERA_TYPE=mock | 无需连接（模拟模式） |

**调试命令：**

```bash
# 列出可用摄像头
python -c "import cv2; [print(f'Camera {i}') for i in range(5) if cv2.VideoCapture(i).isOpened()]"
```

![相机调试]
> **图片标识: deploy-camera** — 相机调试命令输出截图。

### 4.2 HaaS506-HD3 连接

1. USB 供电（5V / 1A）
2. 插入 SIM 卡（中国移动/联通/电信 4G）
3. 等待网络指示灯亮起
4. 配置 `.env` 中的 MQTT 参数
5. 系统管理 → 设备监控 页面查看遥测数据

![硬件连接]
> **图片标识: deploy-haas506** — HaaS506-HD3 实物连接照片。

---

## 五、Core Engine 编译保护

### 5.1 Cython 编译

生产环境发布时，将 Core Engine 编译为 `.so` 文件防止逆向：

```bash
cd aoi_engine
pip install cython  # 首次
python setup.py build_ext --inplace
```

编译成功后，`aoi_engine/` 目录下生成 `.so` 文件，删除 `.py` 源文件即可：

```bash
# 备份源码后删除
rm aoi_engine/*.py  # 保留 __init__.py 或替换为最小版本
```

![Cython编译]
> **图片标识: deploy-cython** — Cython 编译命令输出截图。

### 5.2 验证保护效果

```bash
python -c "from aoi_engine import DefectEngine; print('Core Engine loaded from .so')"
```

![保护验证]
> **图片标识: deploy-protect** — .so 文件加载验证截图。

---

## 六、监控与维护

### 6.1 日志查看

```bash
journalctl -u aoi-vision -f           # systemd 日志
tail -f /var/log/aoi-vision/app.log   # 应用日志
```

### 6.2 数据库备份

```bash
# SQLite
cp aoi_vision.db backups/aoi_vision_$(date +%Y%m%d).db

# PostgreSQL
pg_dump -U aoi_user aoi_vision > backups/aoi_vision_$(date +%Y%m%d).sql
```

### 6.3 健康检查

```bash
# 定时任务
*/5 * * * * curl -s http://localhost:8000/health | grep -q ok || systemctl restart aoi-vision
```

### 6.4 性能监控

```bash
# CPU / 内存
htop

# 磁盘
df -h

# 网络
iftop
```

---

## 七、故障排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 启动报错 ModuleNotFoundError | venv 未激活或依赖缺失 | `source .venv/bin/activate && pip install -r requirements.txt` |
| 数据库连接失败 | 数据库未启动或配置错误 | 检查 `.env` 中 DATABASE_URL |
| 相机无画面 | 相机未连接或驱动问题 | 切换 CAMERA_TYPE=mock 先验证服务 |
| 端口 8000 被占用 | 已有进程监听 | `lsof -ti:8000 \| xargs kill` |
| 权限不足 403 | 未登录或未授权 | 确认 header 中 Authorization 携带有效 token |
| MQTT 连接超时 | 网络或 broker 配置问题 | 检查 DEVICE_GATEWAY_TYPE=mock 先验证 |

---

## 八、文件列表

### 图片占位标识汇总

| 标识 | 章节 | 说明 |
|------|------|------|
| `deploy-clone` | 2.1 | git clone 截图 |
| `deploy-pip-install` | 2.3 | pip install 截图 |
| `deploy-env` | 2.4 | .env 配置截图 |
| `deploy-startup` | 2.5 | uvicorn 启动截图 |
| `deploy-verify` | 2.6 | 浏览器登录页截图 |
| `deploy-nginx` | 3.2 | Nginx 配置截图 |
| `deploy-postgres` | 3.3 | 数据库切换日志截图 |
| `deploy-systemd` | 3.4 | systemctl status 截图 |
| `deploy-camera` | 4.1 | 相机调试截图 |
| `deploy-haas506` | 4.2 | HaaS506 连接照片 |
| `deploy-cython` | 5.1 | Cython 编译截图 |
| `deploy-protect` | 5.2 | .so 加载验证截图 |

---

© 2026 潤芯國際(香港)有限公司 OASYS CORE INTERNATIONAL LIMITED
