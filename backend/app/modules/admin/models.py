"""AOI-Vision v0.1 — 参数枚举模块
日期: 2026-06-17 | 作者: William Chao / OASYS CORE
描述: FieldOption 模型 — 可配置的下拉选项（缺陷类型/产品型号/产线等）
"""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class FieldOption(Base):
    __tablename__ = "field_options"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    option_value: Mapped[str] = mapped_column(String(200), nullable=False)
    option_label: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
