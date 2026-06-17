"""AOI-Vision v0.1 — 硬件层
"""
from app.hardware.camera import BaseCamera, CameraProperties
from app.hardware.device import BaseDeviceGateway, DeviceTelemetry
from app.hardware.factory import create_camera, create_device_gateway, CAMERA_REGISTRY, DEVICE_REGISTRY

__all__ = [
    "BaseCamera", "CameraProperties",
    "BaseDeviceGateway", "DeviceTelemetry",
    "create_camera", "create_device_gateway",
    "CAMERA_REGISTRY", "DEVICE_REGISTRY",
]
