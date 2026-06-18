"""AOI-Vision v0.1 — 硬件工厂 (懒加载版)
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: 根据配置创建相机和网关实例。
      换硬件只改 config，不碰业务代码。
      驱动模块懒加载——没有 OasysCoreCV 时抽象层仍可 import。
"""
from typing import Type
from app.hardware.camera import BaseCamera
from app.hardware.device import BaseDeviceGateway


CAMERA_REGISTRY: dict[str, str] = {
    "uvc": "app.hardware.uvc_camera.UVCCamera",
    "mock": "app.hardware.mock_camera.MockCamera",
    # 未来扩展:
    # "gige": "app.hardware.gige_camera.GigECamera",
    # "hikvision": "app.hardware.hik_camera.HikCamera",
}

DEVICE_REGISTRY: dict[str, str] = {
    "haas506": "app.hardware.haas506_gateway.HaaS506Gateway",
    "mock": "app.hardware.mock_device.MockDeviceGateway",
    # 未来扩展:
    # "modbus": "app.hardware.modbus_gateway.ModbusGateway",
    # "opcua": "app.hardware.opcua_gateway.OPCUAGateway",
}


def _import_class(dotted_path: str) -> Type:
    """懒加载导入类"""
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def create_camera(camera_type: str = "mock", **kwargs) -> BaseCamera:
    """根据类型创建相机实例。
    
    Args:
        camera_type: 'uvc' | 'mock' | 'gige' | 'hikvision' ...
        **kwargs: 传递给具体相机类 (如 index=0, mode='checkerboard')
    
    Example:
        cam = create_camera('mock', mode='checkerboard', width=1920, height=1080)
        cam = create_camera('uvc', index=0)
    """
    dotted = CAMERA_REGISTRY.get(camera_type)
    if dotted is None:
        raise ValueError(f"Unknown camera type: {camera_type}. Available: {list(CAMERA_REGISTRY.keys())}")
    cls = _import_class(dotted)
    return cls(**kwargs)


def create_device_gateway(gateway_type: str = "mock", **kwargs) -> BaseDeviceGateway:
    """根据类型创建设备网关实例。
    
    Args:
        gateway_type: 'haas506' | 'mock' | 'modbus' | 'opcua' ...
        **kwargs: device_id, product_key, ...
    
    Example:
        gw = create_device_gateway('mock', device_id='test-001')
        gw = create_device_gateway('haas506', device_id='hd3-001', product_key='...')
    """
    dotted = DEVICE_REGISTRY.get(gateway_type)
    if dotted is None:
        raise ValueError(f"Unknown device type: {gateway_type}. Available: {list(DEVICE_REGISTRY.keys())}")
    cls = _import_class(dotted)
    return cls(**kwargs)
