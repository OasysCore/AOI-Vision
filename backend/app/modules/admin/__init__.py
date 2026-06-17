"""AOI-Vision v0.1
"""
from app.modules.admin.router import router
from app.modules.admin.service import seed_default_options

__all__ = ["router", "seed_default_options"]
