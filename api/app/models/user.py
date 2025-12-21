"""
用户与认证相关模型

包含 User, UserSession, UserOAuthAccount, UserStats 等表。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin

if TYPE_CHECKING:
    from app.models.book import Book


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin):
    """用户核心表"""

    __tablename__ = "users"

    # 基本信息
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 账户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 会员信息
    membership_tier: Mapped[str] = mapped_column(
        String(20),
        default="FREE",
        nullable=False,
    )
    membership_expire_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 本地化设置
    language: Mapped[str] = mapped_column(String(10), default="zh-CN", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Shanghai", nullable=False)

    # 免费配额
    free_ocr_usage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_gift_reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 邀请码
    invite_code: Mapped[str | None] = mapped_column(
        String(10),
        unique=True,
        nullable=True,
        index=True,
    )

    # 关系
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        lazy="dynamic",
    )
    oauth_accounts: Mapped[list["UserOAuthAccount"]] = relationship(
        "UserOAuthAccount",
        back_populates="user",
        lazy="dynamic",
    )
    books: Mapped[list["Book"]] = relationship(
        "Book",
        back_populates="user",
        lazy="dynamic",
    )
    stats: Mapped["UserStats | None"] = relationship(
        "UserStats",
        back_populates="user",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class UserSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """用户登录会话"""

    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 设备信息
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # web/ios/android
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 状态
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession {self.id} user={self.user_id}>"


class UserOAuthAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """用户 OAuth 第三方账号绑定表"""

    __tablename__ = "user_oauth_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # OAuth 提供商信息
    provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # wechat / google / microsoft / apple
    provider_user_id: Mapped[str] = mapped_column(Text, nullable=False)
    provider_email: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Token 存储 (加密)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 原始用户信息
    raw_profile: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        # 每个提供商的用户 ID 只能绑定一个雅典娜用户
        Index("idx_oauth_provider_user", "provider", "provider_user_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<UserOAuthAccount {self.provider}:{self.provider_user_id}>"


class UserStats(Base, TimestampMixin):
    """用户统计聚合表"""

    __tablename__ = "user_stats"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # 邀请统计
    invite_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 额外配额 (通过邀请获得)
    extra_storage_quota: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 单位: MB
    extra_book_quota: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 使用统计
    storage_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 单位: bytes
    book_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="stats")

    def __repr__(self) -> str:
        return f"<UserStats user={self.user_id}>"


class Invite(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """邀请使用记录"""

    __tablename__ = "invites"

    inviter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invitee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 每个新用户只能被邀请一次
    )

    # 邀请码快照
    code_used: Mapped[str] = mapped_column(String(20), nullable=False)

    # 状态
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending / completed / expired
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 关系
    inviter: Mapped["User"] = relationship("User", foreign_keys=[inviter_id])
    invitee: Mapped["User"] = relationship("User", foreign_keys=[invitee_id])

    def __repr__(self) -> str:
        return f"<Invite {self.inviter_id} -> {self.invitee_id}>"


class UserReadingGoal(Base, TimestampMixin):
    """用户阅读目标"""

    __tablename__ = "user_reading_goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    daily_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    yearly_books: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    def __repr__(self) -> str:
        return f"<UserReadingGoal user={self.user_id}>"


class UserStreak(Base, TimestampMixin):
    """用户阅读连续天数"""

    __tablename__ = "user_streaks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_read_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<UserStreak user={self.user_id} current={self.current_streak}>"


class UserSetting(Base, TimestampMixin, VersionMixin):
    """用户设置 (PowerSync 同步)"""

    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 设置键值对
    key: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        # 每个用户每个 key 只能有一条记录
        {"postgresql_using": "btree"},
    )

    def __repr__(self) -> str:
        return f"<UserSetting {self.user_id}:{self.key}>"
