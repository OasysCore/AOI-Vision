"""AOI-Vision v0.1 — Mock 设备网关
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 无硬件时的模拟设备网关，用于开发测试。
"""
import random
from typing import Any
from datetime import datetime, timezone
from app.hardware.device import BaseDeviceGateway, DeviceTelemetry


class MockDeviceGateway(BaseDeviceGateway):
    """模拟设备网关 — 无硬件依赖"""

    def __init__(self, device_id: str = "mock-device-001"):
        self.device_id = device_id
        self._connected = False
        self._relay1 = False
        self._relay2 = False
        self._start_time = datetime.now(timezone.utc)

    async def connect(self) -> bool:
        self._connected = True
        return True

    async def get_telemetry(self) -> DeviceTelemetry:
        uptime = int((datetime.now(timezone.utc) - self._start_time).total_seconds())
        return DeviceTelemetry(
            device_id=self.device_id,
            online=self._connected,
            signal_strength=random.randint(20, 31),
            temperature=round(random.uniform(35, 50), 1),
            uptime_seconds=uptime,
            relay1_state=self._relay1,
            relay2_state=self._relay2,
            gps_lat=22.5431 + random.uniform(-0.01, 0.01),
            gps_lng=113.929 + random.uniform(-0.01, 0.01),
        )

    async def send_command(self, command: str, params: dict[str, Any] | None = None) -> dict:
        if not self._connected:
            return {"success": False, "error": "Not connected"}
        if command == "set_relay":
            relay_id = params.get("relay", 1) if params else 1
            state = params.get("state", False) if params else False
            if relay_id == 1:
                self._relay1 = state
            else:
                self._relay2 = state
            return {"success": True}
        return {"success": False, "error": f"Unknown: {command}"}

    async def disconnect(self) -> None:
        self._connected = False
