"""
雅典娜 API 核心模块

包含配置、安全、数据库等基础设施代码。
"""

from app.core.config import get_settings, settings

__all__ = ["settings", "get_settings"]
