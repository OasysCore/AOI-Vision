"""AOI-Vision v0.1 — 设备网关抽象层
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 远程设备网关抽象接口。
      换设备只需新增子类，不改业务代码。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime, timezone


@dataclass
class DeviceTelemetry:
    """设备遥测数据"""
    device_id: str = ""
    online: bool = False
    signal_strength: int = 0       # CSQ 0-31
    temperature: float = 0.0        # 设备温度 °C
    uptime_seconds: int = 0
    relay1_state: bool = False      # 继电器1状态
    relay2_state: bool = False
    gps_lat: float = 0.0
    gps_lng: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseDeviceGateway(ABC):
    """设备网关抽象基类"""

    @abstractmethod
    async def connect(self) -> bool:
        """连接设备，返回是否成功"""
        ...

    @abstractmethod
    async def get_telemetry(self) -> DeviceTelemetry:
        """获取设备遥测数据"""
        ...

    @abstractmethod
    async def send_command(self, command: str, params: dict[str, Any] | None = None) -> dict:
        """发送控制指令，返回执行结果"""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        ...
