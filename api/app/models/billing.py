"""
计费与支付相关模型

包含 CreditAccount, CreditLedger, PaymentSession 等表。
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    BigInteger,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class CreditAccount(Base, TimestampMixin):
    """用户积分/钱包账户"""

    __tablename__ = "credit_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Credits 余额
    balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    
    # 钱包余额 (真实货币)
    wallet_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    wallet_currency: Mapped[str] = mapped_column(String(3), default="CNY", nullable=False)

    # 免费额度
    free_credits_monthly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    free_credits_reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<CreditAccount user={self.user_id} balance={self.balance}>"


class CreditLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """积分流水账"""

    __tablename__ = "credit_ledger"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 交易金额
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 正=增加, 负=扣减
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # 交易类型
    transaction_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )  # purchase/consume/refund/gift/invite_reward

    # 交易描述
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 关联信息
    reference_type: Mapped[str | None] = mapped_column(String(30), nullable=True)  # ai_message/ocr_job
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # 元数据
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_credit_ledger_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CreditLedger {self.id} user={self.user_id} amount={self.amount}>"


class CreditProduct(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """积分商品 (充值套餐)"""

    __tablename__ = "credit_products"

    # 商品信息
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 积分数量
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 价格
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="CNY", nullable=False)
    
    # Stripe 产品 ID
    stripe_price_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<CreditProduct {self.name} {self.credits} credits>"


class PaymentSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """支付会话"""

    __tablename__ = "payment_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 支付网关
    gateway: Mapped[str] = mapped_column(String(20), nullable=False)  # stripe/alipay/wechat
    gateway_session_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    gateway_payment_intent: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # 商品信息
    product_type: Mapped[str] = mapped_column(String(30), nullable=False)  # credits/subscription
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # 金额
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # 状态
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending/processing/completed/failed/cancelled/refunded
    
    # 时间戳
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 元数据
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_payment_sessions_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<PaymentSession {self.id} {self.status}>"


class PaymentWebhookEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """支付 Webhook 事件日志"""

    __tablename__ = "payment_webhook_events"

    # 事件信息
    gateway: Mapped[str] = mapped_column(String(20), nullable=False)
    event_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 原始数据
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    # 处理状态
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_webhook_events_gateway_event", "gateway", "event_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<PaymentWebhookEvent {self.event_id}>"


class PricingRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """定价规则"""

    __tablename__ = "pricing_rules"

    # 规则标识
    service_type: Mapped[str] = mapped_column(String(30), nullable=False)  # ai_chat/ocr/translate
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 定价参数
    unit: Mapped[str] = mapped_column(String(20), nullable=False)  # token/page/character
    credits_per_unit: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    min_credits: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # 会员折扣
    free_tier_limit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pro_discount: Mapped[float] = mapped_column(Numeric(3, 2), default=1.0, nullable=False)  # 0.8 = 8折

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("idx_pricing_rules_service", "service_type", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<PricingRule {self.service_type}:{self.name}>"


class FreeQuotaUsage(Base, TimestampMixin):
    """免费配额使用记录"""

    __tablename__ = "free_quota_usage"

    # 复合主键
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    quota_type: Mapped[str] = mapped_column(String(30), primary_key=True)  # ocr_pages/ai_tokens
    period: Mapped[str] = mapped_column(String(7), primary_key=True)  # YYYY-MM

    # 使用量
    used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    limit: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<FreeQuotaUsage {self.user_id} {self.quota_type} {self.used}/{self.limit}>"
