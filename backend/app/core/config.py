"""AOI-Vision v0.1
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aoi_vision"
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    UPLOAD_DIR: str = "./uploads"
    CAMERA_INDEX: int = 0
    CAMERA_TYPE: str = "mock"       # mock | uvc | gige | hikvision | ...
    DEVICE_GATEWAY_TYPE: str = "mock"  # mock | haas506 | modbus | opcua | ...

    class Config:
        env_file = ".env"

settings = Settings()
