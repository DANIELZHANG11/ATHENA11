"""
系统配置与功能开关模型

包含 SystemSetting, FeatureFlag, Translation 等表。
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SystemSetting(Base, TimestampMixin):
    """系统配置表"""

    __tablename__ = "system_settings"

    # 配置键
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    
    # 配置值
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    
    # 描述
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 是否可被 API 修改
    is_readonly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<SystemSetting {self.key}>"


class FeatureFlag(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """功能开关"""

    __tablename__ = "feature_flags"

    # 开关标识
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 开关状态
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 灰度发布
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=100, nullable=False)  # 0-100
    
    # 白名单/黑名单
    whitelist_user_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    blacklist_user_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    
    # 条件
    conditions: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # 例: {"membership_tier": ["PRO", "ENTERPRISE"], "app_version": ">=2.0.0"}

    def __repr__(self) -> str:
        return f"<FeatureFlag {self.name} enabled={self.is_enabled}>"


class Translation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """多语言翻译表 (Tolgee 备份/同步)"""

    __tablename__ = "translations"

    # 翻译键
    key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(50), default="common", nullable=False)
    
    # 语言
    language: Mapped[str] = mapped_column(String(10), nullable=False)  # zh-CN/en-US
    
    # 翻译值
    value: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 来源
    source: Mapped[str] = mapped_column(String(20), default="tolgee", nullable=False)  # tolgee/manual

    __table_args__ = (
        Index("idx_translations_key_lang", "key", "language", unique=True),
        Index("idx_translations_namespace", "namespace"),
    )

    def __repr__(self) -> str:
        return f"<Translation {self.key}:{self.language}>"


class OcrJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """OCR 任务表"""

    __tablename__ = "ocr_jobs"

    # 关联书籍
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # 任务状态
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending/processing/completed/failed

    # 进度
    total_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100

    # 结果
    output_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # 双层 PDF Key
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 时间戳
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Celery 任务 ID
    celery_task_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 计费
    credits_consumed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<OcrJob {self.id} book={self.book_id} {self.status}>"
